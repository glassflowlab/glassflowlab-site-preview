#!/usr/bin/env python3
"""
AEO 升級:為 glassflowlab-site-preview 注入 Schema.org JSON-LD。

處理全部商品(從 products-index.json)+ 分類頁(從 category/ 目錄)+ 首頁。

用法:
  python3 inject-aeo.py
"""
import json
import re
from pathlib import Path

ROOT = Path("/tmp/glassflowlab-site-preview")
BASE_URL = "https://glassflowlab.github.io/glassflowlab-site-preview"

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

# 自訂 description(給主力/有特殊用途的)
HERO_DESCRIPTIONS = {
    "100四方瓶": "寬口方型玻璃果醬罐,適合果醬、抹醬、樣品分裝等食品包裝",
    "138蜂蜜瓶": "玻璃蜂蜜瓶,適合自製蜂蜜或品牌精裝",
    "250醬菜瓶": "寬口玻璃醬菜瓶,適合泡菜、醃漬品、果醬",
    "300透明梅酒瓶": "透明玻璃梅酒瓶,適合自釀梅酒、果露、精釀飲品",
    "250透明精緻油品瓶": "透明精緻玻璃油品瓶,適合橄欖油、醋、醬料等精緻包裝",
}

def detect_category(name: str) -> str:
    if "蜂蜜" in name: return "玻璃瓶 > 蜂蜜瓶"
    if "油品" in name: return "玻璃瓶 > 油品瓶"
    if "梅酒" in name or "冷泡" in name or "隨身" in name: return "玻璃瓶 > 飲品瓶"
    if "醬菜" in name or "泡菜" in name: return "玻璃瓶 > 醬菜瓶"
    if "四方" in name or "四角" in name: return "玻璃瓶 > 寬口方瓶"
    if "香氛" in name or "樣品" in name: return "玻璃瓶 > 香氛/樣品瓶"
    if "珍釀" in name or "醷醇" in name or "麻油" in name: return "玻璃瓶 > 精釀瓶"
    if "海苔" in name: return "玻璃瓶 > 食品瓶"
    if "美乃滋" in name: return "玻璃瓶 > 醬料瓶"
    if "六號" in name or "五號" in name or "鑼口" in name: return "玻璃瓶 > 寬口圓瓶"
    if "小圓" in name or "小目" in name or "大目" in name or "大耳" in name: return "玻璃瓶 > 圓瓶"
    if "六角" in name: return "玻璃瓶 > 六角瓶"
    return "玻璃瓶 > 食品包裝"

def auto_description(name: str, category: str) -> str:
    """根據分類 + 名稱自動生成 description。"""
    if name in HERO_DESCRIPTIONS:
        return HERO_DESCRIPTIONS[name]
    # 從名稱抓容量數字
    cap = re.search(r'(\d+(?:\.\d+)?)', name)
    cap_str = f"容量約 {cap.group(1)}ml" if cap else ""
    templates = {
        "玻璃瓶 > 蜂蜜瓶": f"玻璃蜂蜜瓶{cap_str},窄口設計方便倒出,適合蜂蜜、果醬等食品包裝",
        "玻璃瓶 > 油品瓶": f"玻璃油品瓶{cap_str},適合橄欖油、醋、醬料等精緻包裝",
        "玻璃瓶 > 飲品瓶": f"玻璃飲品瓶{cap_str},適合梅酒、果露、茶飲等精釀飲品",
        "玻璃瓶 > 醬菜瓶": f"寬口玻璃醬菜瓶{cap_str},適合泡菜、醃漬品、果醬",
        "玻璃瓶 > 寬口方瓶": f"寬口方型玻璃瓶{cap_str},適合果醬、抹醬、樣品分裝",
        "玻璃瓶 > 香氛/樣品瓶": f"小容量玻璃樣品瓶,適合香氛、精油、樣品分裝",
        "玻璃瓶 > 精釀瓶": f"精釀玻璃瓶{cap_str},適合珍釀酒、麻油等精緻包裝",
        "玻璃瓶 > 食品瓶": f"玻璃食品瓶{cap_str},適合海苔、茶葉等食品包裝",
        "玻璃瓶 > 醬料瓶": f"玻璃醬料瓶{cap_str},適合美乃滋、沙拉醬等濃稠醬料",
        "玻璃瓶 > 寬口圓瓶": f"寬口圓型玻璃瓶{cap_str},適合食品包裝、醃漬品",
        "玻璃瓶 > 圓瓶": f"圓型玻璃瓶{cap_str},適合食品、醬料等包裝",
        "玻璃瓶 > 六角瓶": f"六角玻璃瓶{cap_str},獨特造型適合精緻食品包裝",
    }
    return templates.get(category, f"玻璃容器{cap_str},適合食品包裝")

def parse_specs_from_html(html: str) -> list:
    """從商品頁 HTML 的 <table> 規格表抓出 PropertyValue 用的 key-value pairs。"""
    table_match = re.search(r'<section[^>]*id="specs"[^>]*>(.*?)</section>', html, re.DOTALL)
    if not table_match:
        return []
    table_html = table_match.group(1)
    rows = re.findall(r'<tr>\s*<th>(.*?)</th>\s*<td>(.*?)</td>\s*</tr>', table_html, re.DOTALL)
    props = []
    skip_keys = {"商品名稱", "貨號", "售價"}
    for k, v in rows:
        k = re.sub(r'<[^>]+>', '', k).strip()
        v = re.sub(r'<[^>]+>', '', v).strip()
        if k in skip_keys:
            continue
        if k and v:
            props.append({"@type": "PropertyValue", "name": k, "value": v})
    return props

def make_product_jsonld(product: dict, specs: list) -> dict:
    name = product["name"]
    slug = product["slug"]
    category = detect_category(name)
    description = auto_description(name, category)
    spec_summary = []
    for s in specs:
        if s["name"] in ("容量", "尺寸"):
            spec_summary.append(f"{s['name']} {s['value']}")
    desc_bits = [description]
    if spec_summary:
        desc_bits.append("規格:" + "; ".join(spec_summary))
    desc_bits.append(f"1 箱 {product['boxQuantity']} 支,售價 NT${product['price']:,}。")
    return {
        "@context": "https://schema.org",
        "@type": "Product",
        "name": name,
        "description": " ".join(desc_bits),
        "image": f"{BASE_URL}/{product['image']}",
        "sku": slug,
        "mpn": slug,
        "brand": {"@type": "Brand", "name": "玻璃小店 GlassFlow Lab"},
        "category": category,
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

def make_itemlist_jsonld(products: list, list_name: str, description: str) -> dict:
    return {
        "@context": "https://schema.org",
        "@type": "ItemList",
        "name": list_name,
        "description": description,
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

def remove_existing_jsonld(html: str) -> str:
    """移除所有現有的 application/ld+json script(避免重複)。"""
    return re.sub(r'<script type="application/ld\+json">.*?</script>\s*', '', html, flags=re.DOTALL)

def inject_jsonld(html: str, jsonld: dict, position: str = "before-style") -> str:
    """注入 JSON-LD。position: 'before-style' 或 'before-head-close'"""
    jsonld_str = json.dumps(jsonld, ensure_ascii=False, indent=2)
    script_tag = f'<script type="application/ld+json">\n{jsonld_str}\n</script>\n'
    if position == "before-style" and '<style>' in html:
        return html.replace('<style>', script_tag + '  <style>', 1)
    elif '</head>' in html:
        return html.replace('</head>', script_tag + '</head>', 1)
    return html

def detect_category_from_name(name: str) -> str:
    """分類頁檔名(寬口瓶 / 窄口瓶) → 對應分類描述"""
    if name == "寬口瓶":
        return ("寬口玻璃瓶系列", "寬口設計方便取用,適合果醬、泡菜、醃漬品、樣品分裝等需要寬口取用的食品包裝。")
    elif name == "窄口瓶":
        return ("窄口玻璃瓶系列", "窄口設計便於控制流量,適合蜂蜜、醬料、油品、梅酒、茶飲等液態或精緻包裝。")
    return (name, "")

def main():
    products_index = json.loads((ROOT / "products-index.json").read_text())
    print(f"[INFO] products-index.json: {len(products_index)} 個商品")

    # 1. 為每個商品頁注入 Product JSON-LD
    success = 0
    fail = 0
    for product in products_index:
        slug = product["slug"]
        html_path = ROOT / "products" / f"{slug}.html"
        if not html_path.exists():
            print(f"[WARN] 找不到 HTML: {product['name']}")
            fail += 1
            continue
        html = html_path.read_text()
        html = remove_existing_jsonld(html)
        specs = parse_specs_from_html(html)
        jsonld = make_product_jsonld(product, specs)
        new_html = inject_jsonld(html, jsonld)
        html_path.write_text(new_html)
        success += 1
    print(f"[OK]   商品頁: {success} 成功, {fail} 失敗")

    # 2. 為分類頁注入 ItemList
    for cat_path in sorted((ROOT / "category").glob("*.html")):
        cat_name = cat_path.stem
        cat_title, cat_desc = detect_category_from_name(cat_name)
        # 找出屬於這個分類的商品(用 detect_category 判斷)
        # 但這不精準 — 改用名稱 pattern
        cat_products = []
        for p in products_index:
            n = p["name"]
            if cat_name == "寬口瓶":
                if any(k in n for k in ["四方", "四角", "大耳", "小目", "大目", "六角", "小圓", "海苔", "美乃滋", "醬菜", "泡菜", "六號", "五號", "鑼口"]):
                    cat_products.append(p)
            elif cat_name == "窄口瓶":
                if any(k in n for k in ["油品", "蜂蜜", "梅酒", "冷泡", "隨身", "香氛", "樣品", "珍釀", "醷醇", "麻油"]):
                    cat_products.append(p)
        if cat_products:
            list_jsonld = make_itemlist_jsonld(cat_products, cat_title, cat_desc)
            html = cat_path.read_text()
            html = remove_existing_jsonld(html)
            new_html = inject_jsonld(html, list_jsonld)
            cat_path.write_text(new_html)
            print(f"[OK]   分類頁 {cat_name}: 注入 ItemList({len(cat_products)} 個商品)")

    # 3. 為 index.html 注入 Organization + 全部商品 ItemList
    index_path = ROOT / "index.html"
    index_html = index_path.read_text()
    # 移除舊的 JSON-LD(避免重複)
    index_html = re.sub(r'<script type="application/ld\+json">.*?</script>\s*', '', index_html, flags=re.DOTALL)
    index_html = inject_jsonld(index_html, ORG_JSONLD)
    itemlist = make_itemlist_jsonld(products_index, "玻璃小店所有商品", "玻璃小店全系列玻璃容器,涵蓋寬口瓶與窄口瓶,適合各種食品包裝需求。")
    index_html = inject_jsonld(index_html, itemlist)
    index_path.write_text(index_html)
    print(f"[OK]   index.html: Organization + ItemList({len(products_index)} 個商品)")

    print(f"\n[DONE] 全部 AEO 注入完成")

if __name__ == "__main__":
    main()