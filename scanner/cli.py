import asyncio
import sys
import json
import csv
from pathlib import Path
import os
from typing import List
from tabulate import tabulate
from .collector import scan_many


TARGET_DOMAINS = {"alexametrics.com"}


def read_domains_file(path: Path) -> List[str]:
    # Temel teşhis
    print(f"Dosya yolu: {path} | var mi: {path.exists()} | mutlak: {path.resolve()}")
    try:
        size = path.stat().st_size if path.exists() else -1
        print(f"Dosya boyutu: {size} byte")
    except Exception as e:
        print(f"Dosya boyutu okunamadi: {e}")

    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
        lines = text.splitlines()
    except Exception as e:
        print(f"read_text hatasi: {e} | ikili yedek okunuyor")
        try:
            with open(path, "rb") as f:
                data = f.read()
            lines = data.decode("utf-8", errors="ignore").split("\n")
        except Exception as e2:
            print(f"Yedek okuma da basarisiz: {e2}")
            lines = []

    # Teşhis: ilk 3 satırı göster (stderr yerine stdio)
    sample = [repr(l) for l in lines[:3]]
    print(f"Dosyadan {len(lines)} satir okundu. Ornek: {sample}")

    urls = []
    skipped = 0
    for line in lines:
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        if "://" in s:
            urls.append(s)
        else:
            skipped += 1
    if skipped:
        print(f"Uyari: {skipped} satirda http/https şemasi yoktu ve atlandi (artik otomatik eklenmiyor).")
    return urls


def write_output(results, out_path: str | None, fmt: str = "json"):
    if not out_path:
        return
    # Sadece eslesme bulunan kayitlari yaz
    filtered = [r for r in results if r.get("matched")]
    p = Path(out_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    if fmt == "json":
        p.write_text(json.dumps(filtered, ensure_ascii=False, indent=2), encoding="utf-8")
    elif fmt == "csv":
        with p.open("w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["url", "matched", "domain", "request_url"])
            for r in filtered:
                for m in r.get("matches", []):
                    writer.writerow([r.get("url"), True, m.get("domain", ""), m.get("request_url", "")])
    else:
        print(f"Desteklenmeyen format: {fmt}. json|csv kullanin.")


async def main(
    domains_file: str,
    concurrency: int = 5,
    out_path: str | None = None,
    fmt: str = "json",
    *,
    page_timeout_ms: int = 30000,
    extra_wait_ms: int = 3000,
    verbose: bool = False,
):
    urls = read_domains_file(Path(domains_file))
    if not urls:
        print(f"Uyari: {domains_file} icinden hic URL okunamadi. Dosya bos mu?")
        return
    print(f"Toplam {len(urls)} URL okundu. Ilk 3 ornek: {urls[:3]}")
    results = await scan_many(
        urls,
        TARGET_DOMAINS,
        concurrency=concurrency,
        page_timeout_ms=page_timeout_ms,
        extra_wait_ms=extra_wait_ms,
        verbose=verbose,
    )

    # Dosyaya yaz
    write_output(results, out_path, fmt)

    table = []
    for r in results:
        if r["matched"]:
            detail = " | ".join(f"{m['domain']} -> {m['request_url']}" for m in r["matches"])
        else:
            detail = "-"
        table.append([r["url"], "YES" if r["matched"] else "NO", detail])

    print(tabulate(table, headers=["URL", "ALEXAMETRICS JS?", "Detay"], tablefmt="github"))


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Kullanim: python -m scanner.cli domain.txt [concurrency] [--out /path/file.json] [--format json|csv] [--timeout-ms 30000] [--extra-wait-ms 3000] [--verbose]")
        sys.exit(1)
    domains_file = sys.argv[1]
    # Basit arg parse
    conc = 5
    out_path = None
    fmt = "json"
    page_timeout_ms = 30000
    extra_wait_ms = 3000
    verbose = False
    i = 2
    while i < len(sys.argv):
        arg = sys.argv[i]
        if arg.isdigit():
            conc = int(arg)
        elif arg == "--out" and i + 1 < len(sys.argv):
            out_path = sys.argv[i + 1]
            i += 1
        elif arg == "--format" and i + 1 < len(sys.argv):
            fmt = sys.argv[i + 1].lower()
            i += 1
        elif arg == "--timeout-ms" and i + 1 < len(sys.argv):
            page_timeout_ms = int(sys.argv[i + 1])
            i += 1
        elif arg == "--extra-wait-ms" and i + 1 < len(sys.argv):
            extra_wait_ms = int(sys.argv[i + 1])
            i += 1
        elif arg == "--verbose":
            verbose = True
        else:
            print(f"Bilinmeyen arguman atlandi: {arg}")
        i += 1

    asyncio.run(
        main(
            domains_file,
            concurrency=conc,
            out_path=out_path,
            fmt=fmt,
            page_timeout_ms=page_timeout_ms,
            extra_wait_ms=extra_wait_ms,
            verbose=verbose,
        )
    )


