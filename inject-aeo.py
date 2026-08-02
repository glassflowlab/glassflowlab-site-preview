#!/usr/bin/env python3
"""
AEO 升級:為 glassflowlab-site-preview 注入 Schema.org JSON-LD。

讀 products-index.json,從每個商品頁 HTML 的 <table> 規格自動抓出容量/尺寸/重量等,
生成 Schema.org Product + Organization + ItemList JSON-LD,注入到 head 的 <style> 之前。

用法:
  python3 inject-aeo.py
"""
import json
import re
from pathlib import Path

ROOT = Path("/tmp/glassflowlab-site-preview")
BASE_URL = "https://glassflowlab.github.io/glassflowlab-site-preview"

HERO_SLUGS = {
    "100四方瓶": "寬口果醬罐,適合果醬、抹醬、樣品分裝",
    "138蜂蜜瓶": "玻璃蜂蜜瓶,適合自製蜂蜜或品牌精裝",
    "250醬菜瓶": "寬口醬菜瓶,適合泡菜、醃漬品、果醬",
    "300透明梅酒瓶": "透明玻璃梅酒瓶,適合自釀梅酒、果露、精釀飲品",
    "250透明精緻油品瓶": "透明精緻油品瓶,適合橄欖油、醋、醬料等精緻包裝",
}

ORG_JSONLD = {
    "@context": "https://schema.org",
    "@type": "Organization",
    "name": "玻璃小店 GlassFlow Lab",
    "alternateName": "GlassFlow Lab",
    "url": f"{BASE_URL}/",
    "logo": f"{BASE_URL}/assets/common/logo.png",
    "description": "台灣玻璃容器供應商,提供果醬、蜂蜜、醬料、油品、梅酒等專用玻璃瓶罐。現貨供應、可自取或宅配。",
    "contactPoint": {
        "@type": "ContactPoint",
        "contactType": "customer service",
        "url": "https://line.me/R/ti/p/@lrg1884b",
        "availableLanguage": ["zh-Hant"]
    },
    "address": {
        "@type": "PostalAddress",
        "addressCountry": "TW"
    }
}

def parse_specs_from_html(html: str) -> dict:
    """從商品頁 HTML 的 <table> 規格表抓出 PropertyValue 用的 key-value pairs。"""
    table_match = re.search(r'<section[^>]*id="specs"[^>]*>(.*?)</section>', html, re.DOTALL)
    if not table_match:
        return []
    table_html = table_match.group(1)
    rows = re.findall(r'<tr>\s*<th>(.*?)</th>\s*<td>(.*?)</td>\s*</tr>', table_html, re.DOTALL)
    props = []
    skip_keys = {"商品名稱", "貨號", "售價"}  # 這些已在 Product.name/sku/offers.price
    for k, v in rows:
        k = re.sub(r'<[^>]+>', '', k).strip()
        v = re.sub(r'<[^>]+>', '', v).strip()
        if k in skip_keys:
            continue
        if k and v:
            props.append({"@type": "PropertyValue", "name": k, "value": v})
    return props

def detect_category(name: str) -> str:
    if "蜂蜜" in name: return "玻璃瓶 > 蜂蜜瓶"
    if "油品" in name: return "玻璃瓶 > 油品瓶"
    if "梅酒" in name or "冷泡" in name or "隨身" in name: return "玻璃瓶 > 飲品瓶"
    if "醬菜" in name or "泡菜" in name: return "玻璃瓶 > 醬菜瓶"
    if "四方" in name or "四角" in name: return "玻璃瓶 > 寬口方瓶"
    if "香氛" in name or "樣品" in name: return "玻璃瓶 > 香氛/樣品瓶"
    if "珍釀" in name or "醷醇" in name or "麻油" in name: return "玻璃瓶 > 精釀瓶"
    return "玻璃瓶 > 食品包裝"

def make_product_jsonld(product: dict, specs: list) -> dict:
    name = product["name"]
    slug = product["slug"]
    description_bits = [HERO_SLUGS.get(name, "玻璃容器,適合食品包裝。")]
    # 把規格摘要寫進 description,讓 ChatGPT 讀得到
    spec_summary = []
    for s in specs:
        if s["name"] in ("容量", "尺寸"):
            spec_summary.append(f"{s['name']} {s['value']}")
    if spec_summary:
        description_bits.append("規格:" + "; ".join(spec_summary))
    description_bits.append(f"1 箱 {product['boxQuantity']} 支,售價 NT${product['price']:,}。")
    return {
        "@context": "https://schema.org",
        "@type": "Product",
        "name": name,
        "description": " ".join(description_bits),
        "image": f"{BASE_URL}/{product['image']}",
        "sku": slug,
        "mpn": slug,
        "brand": {"@type": "Brand", "name": "玻璃小店 GlassFlow Lab"},
        "category": detect_category(name),
        "additionalProperty": specs,
        "offers": {
            "@type": "Offer",
            "price": str(product["price"]),
            "priceCurrency": "TWD",
            "priceValidUntil": "2027-12-31",
            "availability": "https://schema.org/InStock",
            "itemCondition": "https://schema.org/NewCondition",
            "url": f"{BASE_URL}/{product['url']}",
            "seller": {"@type": "Organization", "name": "玻璃小店"}
        }
    }

def make_itemlist_jsonld(products: list) -> dict:
    return {
        "@context": "https://schema.org",
        "@type": "ItemList",
        "name": "玻璃小店主打商品",
        "description": "果醬、蜂蜜、醬料、油品、梅酒等食品包裝用玻璃瓶。",
        "numberOfItems": len(products),
        "itemListElement": [
            {
                "@type": "ListItem",
                "position": i + 1,
                "item": {
                    "@type": "Product",
                    "name": p["name"],
                    "url": f"{BASE_URL}/{p['url']}",
                    "image": f"{BASE_URL}/{p['image']}",
                    "offers": {
                        "@type": "Offer",
                        "price": str(p["price"]),
                        "priceCurrency": "TWD"
                    }
                }
            }
            for i, p in enumerate(products)
        ]
    }

def inject_jsonld(html: str, jsonld: dict) -> str:
    """在 <head> 裡的 <style> 之前注入 JSON-LD script。"""
    jsonld_str = json.dumps(jsonld, ensure_ascii=False, indent=2)
    script_tag = f'<script type="application/ld+json">\n{jsonld_str}\n</script>\n'
    # 在 <style> 之前插入
    if '<style>' in html:
        return html.replace('<style>', script_tag + '  <style>', 1)
    elif '</head>' in html:
        return html.replace('</head>', script_tag + '</head>', 1)
    else:
        return html

def main():
    products_index = json.loads((ROOT / "products-index.json").read_text())
    hero_products = [p for p in products_index if p["name"] in HERO_SLUGS]
    print(f"[INFO] 找到 {len(hero_products)} 個主力商品")

    # 1. 為每個主力商品頁注入 Product JSON-LD
    for product in hero_products:
        slug = product["slug"]
        html_path = ROOT / "products" / f"{slug}.html"
        if not html_path.exists():
            print(f"[WARN] 找不到 {html_path}")
            continue
        html = html_path.read_text()
        specs = parse_specs_from_html(html)
        jsonld = make_product_jsonld(product, specs)
        new_html = inject_jsonld(html, jsonld)
        html_path.write_text(new_html)
        print(f"[OK]   {product['name']}: 注入 {len(specs)} 個規格")

    # 2. 為 index.html 注入 Organization + ItemList
    index_path = ROOT / "index.html"
    index_html = index_path.read_text()
    # 先注入 Organization
    index_html = inject_jsonld(index_html, ORG_JSONLD)
    # 再注入 ItemList(在 Organization 之後)
    itemlist = make_itemlist_jsonld(hero_products)
    index_html = inject_jsonld(index_html, itemlist)
    index_path.write_text(index_html)
    print(f"[OK]   index.html: 注入 Organization + ItemList(5 個商品)")

    print("\n[DONE] 全部 JSON-LD 注入完成")

if __name__ == "__main__":
    main()