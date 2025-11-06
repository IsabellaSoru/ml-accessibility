import argparse
import json
import re
import statistics
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

GENERIC_LINKS = {
    "clicca qui", "click here", "read more", "scopri di più", "learn more",
    "qui", "more", "leggi di più", "approfondisci", "continua", "dettagli",
    "vai", "open", "info", "link", "discover", "see more", "view more"
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
}

def fetch_html(url: str) -> str:
    resp = requests.get(url, headers=HEADERS, timeout=15)
    resp.raise_for_status()
    return resp.text

def parse_dom(html: str):
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html, "html.parser")
    # rimuovi elementi inutili per la leggibilità
    for tag in soup(["script","style","noscript","svg","meta","link","iframe"]):
        tag.decompose()
    # elimina blocchi tipici di navigazione/legali
    selectors = [
        "nav","header","footer",
        ".cookie",".cookies",".gdpr",".consent",".banner",
        ".breadcrumb",".menu",".navbar",".offcanvas",
        ".newsletter",".modal",".social",".credits",".legal",".policy",".privacy",".cookie-policy"
    ]
    for sel in selectors:
        for el in soup.select(sel):
            el.decompose()
    return soup

# ---------- IMAGES ----------
def extract_images(soup: BeautifulSoup, base_url: str):
    imgs = []
    for img in soup.find_all("img"):
        src = img.get("src") or ""
        if not src:
            continue
        # skip tiny data URIs
        if src.startswith("data:"):
            continue
        role = (img.get("role") or "").strip().lower()
        alt = (img.get("alt") or "").strip()
        imgs.append({
            "img_src": urljoin(base_url, src),
            "role": role,
            "alt_text": alt
        })
    return imgs

def evaluate_images_baseline(images):
    """
    Regola semplice:
    - Se <img> NON è presentational e ha alt mancante o troppo corto → issue.
    """
    issues = []
    total = len(images)
    for im in images:
        role = im["role"]
        alt = im["alt_text"]
        # presentational / decorative hints
        is_presentational = role in {"presentation", "none"} or alt == ""  # empty alt often used for decorative
        # If not explicitly decorative and alt is missing/too short, flag
        if not is_presentational and len(alt) < 5:
            issues.append({"img_src": im["img_src"], "reason": "missing_or_short_alt"})
    score = 1.0
    if total > 0:
        score = max(0.0, 1.0 - (len(issues) / total))
    return {"score": round(score, 2), "issues": issues, "total": total}

# ---------- LINKS ----------
def clean_text(t: str) -> str:
    return re.sub(r"\s+", " ", (t or "").strip()).lower()

def extract_links(soup: BeautifulSoup, base_url: str):
    links = []
    for a in soup.find_all("a"):
        text = clean_text(a.get_text(" ").strip())
        href = a.get("href") or ""
        if not href:
            continue
        links.append({
            "anchor_text": text,
            "href": urljoin(base_url, href)
        })
    return links

def evaluate_links_baseline(links):
    def is_contact(href, text):
        t = (text or "").lower()
        h = (href or "").lower()
        return h.startswith("tel:") or h.startswith("mailto:") or "@" in h or "@" in t

    def is_lang_switch(text):
        t = (text or "").strip().lower()
        return t in {"it","ita","en","eng","de","fr","es"}

    generic = []
    seen = set()
    total = 0
    for lk in links:
        txt = lk["anchor_text"]
        href = lk["href"]
        key = (txt, href)
        if key in seen:  # de-duplica
            continue
        seen.add(key)
        total += 1

        tokens = [t for t in txt.split() if t.isalpha()]
        # esenzioni: lingua/contatti/icone vuote
        if is_lang_switch(txt) or is_contact(href, txt) or txt == "":
            continue

        is_generic = (txt in GENERIC_LINKS) or (len(tokens) < 2)
        if is_generic:
            generic.append({"text": txt, "href": href})

    score = 1.0 if total == 0 else max(0.0, 1.0 - (len(generic) / total))
    return {"score": round(score, 2), "generic_links": generic, "total": total}

# ---------- READABILITY ----------
def split_sentences(text: str):
    # splitter super semplice (basta per baseline)
    return [s.strip() for s in re.split(r"[.!?]+", text) if s.strip()]

def avg_sentence_length_words(text: str) -> float:
    sentences = split_sentences(text)
    if not sentences:
        return 0.0
    lengths = []
    for s in sentences:
        words = [w for w in re.findall(r"[A-Za-zÀ-ÖØ-öø-ÿ']+", s)]
        if words:
            lengths.append(len(words))
    return statistics.mean(lengths) if lengths else 0.0

def avg_word_length(text: str) -> float:
    words = [w for w in re.findall(r"[A-Za-zÀ-ÖØ-öø-ÿ']+", text)]
    if not words:
        return 0.0
    return statistics.mean(len(w) for w in words)

def extract_paragraphs(soup: BeautifulSoup, limit=40):
    paras = []
    for i, p in enumerate(soup.find_all(["p", "li"])):
        txt = clean_text(p.get_text(" ").strip())
        if len(txt) < 40:  # ignora pezzi troppo corti/rumore
            continue
        paras.append({"id": f"node-{i}", "text": txt})
        if len(paras) >= limit:
            break
    return paras

def label_readability(text: str):
    """
    Heuristics:
      - Easy: avg sentence len <= 15 AND avg word len <= 4.7
      - Difficult: avg sentence len > 25 OR avg word len > 5.5
      - Medium: altrimenti
    """
    asl = avg_sentence_length_words(text)
    awl = avg_word_length(text)
    if asl <= 15 and awl <= 4.7:
        return "easy"
    if asl > 25 or awl > 5.5:
        return "difficult"
    return "medium"

def evaluate_readability_baseline(paragraphs):
    labeled = []
    total = len(paragraphs)
    difficult_segments = []
    easy_cnt = medium_cnt = difficult_cnt = 0
    for p in paragraphs:
        lab = label_readability(p["text"])
        labeled.append({"id": p["id"], "label": lab, "snippet": p["text"][:160] + ("..." if len(p["text"]) > 160 else "")})
        if lab == "easy": easy_cnt += 1
        elif lab == "medium": medium_cnt += 1
        else:
            difficult_cnt += 1
            difficult_segments.append({"id": p["id"], "snippet": p["text"][:160] + ("..." if len(p["text"]) > 160 else "")})
    # score: 1 - quota di 'difficult'
    score = 1.0
    if total > 0:
        score = max(0.0, 1.0 - (difficult_cnt / total))
    return {
        "score": round(score, 2),
        "distribution": {"easy": easy_cnt, "medium": medium_cnt, "difficult": difficult_cnt, "total": total},
        "difficult": difficult_segments
    }

# ---------- AGGREGATION ----------
def aggregate_scores(img_score, read_score, link_score):
    w_img, w_read, w_link = 0.35, 0.35, 0.30
    final_score = (w_img * img_score) + (w_read * read_score) + (w_link * link_score)
    if final_score >= 0.80:
        rating = "Compliant"
    elif final_score >= 0.60:
        rating = "Partially compliant"
    else:
        rating = "Non-compliant"
    return round(final_score, 2), rating

def build_suggestions(img_res, read_res, link_res):
    suggestions = []
    if img_res["issues"]:
        suggestions.append("Add descriptive alt text to informative images (those without or with too-short alt).")
    if read_res["distribution"]["difficult"] > 0:
        suggestions.append("Simplify paragraphs labeled 'difficult' (shorter sentences, simpler vocabulary).")
    if link_res["generic_links"]:
        suggestions.append("Replace generic anchors (e.g., 'click here') with descriptive link text.")
    if not suggestions:
        suggestions.append("Good job: no major baseline issues detected.")
    return suggestions

# ---------- MAIN ----------
def run(url: str):
    html = fetch_html(url)
    soup = parse_dom(html)

    images = extract_images(soup, url)
    links = extract_links(soup, url)
    paragraphs = extract_paragraphs(soup)

    img_res = evaluate_images_baseline(images)
    link_res = evaluate_links_baseline(links)
    read_res = evaluate_readability_baseline(paragraphs)

    final_score, final_rating = aggregate_scores(img_res["score"], read_res["score"], link_res["score"])
    suggestions = build_suggestions(img_res, read_res, link_res)

    result = {
        "url": url,
        "modules": {
            "images": img_res,
            "readability": read_res,
            "links": link_res
        },
        "final_score": final_score,
        "final_rating": final_rating,
        "suggestions": suggestions
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Baseline web accessibility evaluation (no ML).")
    parser.add_argument("--url", required=True, help="Web page URL to evaluate")
    args = parser.parse_args()
    run(args.url)
