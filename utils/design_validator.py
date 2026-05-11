"""
Design Validator v2.1
=====================
解析 LLM 回應中的三個方案 JSON，
各自進行 Grammar 驗證，保留 span 和 roof 資訊供視覺化使用。
"""
 
import json
import re
from utils.connection_grammar import validate_configuration, format_validation_report
 
 
def extract_design_json(reply: str) -> dict | None:
    match = re.search(r"<DESIGN_JSON>([\s\S]*?)</DESIGN_JSON>", reply)
    if not match:
        return None
    try:
        return json.loads(match.group(1).strip())
    except json.JSONDecodeError:
        return None
 
 
def expand_blocks(scheme: dict) -> list:
    expanded = []
    for block in scheme.get("blocks", []):
        qty = block.get("quantity", 1)
        for _ in range(qty):
            expanded.append({
                "id":       block.get("id", ""),
                "name":     block.get("name", block.get("id", "").split("_")[-1]),
                "category": block.get("category", ""),
                "series":   block.get("series", ""),
            })
    return expanded
 
 
def validate_all_schemes(design_json: dict) -> dict:
    results = {}
    all_valid = True
    invalid_schemes = []
 
    for scheme_key in ["scheme_a", "scheme_b", "scheme_c"]:
        scheme = design_json.get(scheme_key, {})
        if not scheme:
            results[scheme_key] = {
                "is_valid": False,
                "validation": {
                    "errors": [{"rule_id": "E00", "message": f"{scheme_key} 方案資料缺失"}],
                    "warnings": [], "assembly_order": [],
                    "summary": {}, "fabrication_notes": [], "ties": {}
                },
                "blocks": [],
                "span":   "M",
                "roof":   "flat",
            }
            all_valid = False
            invalid_schemes.append(scheme_key)
            continue
 
        blocks  = expand_blocks(scheme)
        stories = scheme.get("stories", 1)
        validation = validate_configuration(blocks, stories=stories)
 
        results[scheme_key] = {
            "is_valid":   validation["is_valid"],
            "validation": validation,
            "blocks":     blocks,
            "span":       scheme.get("span", "M"),
            "roof":       scheme.get("roof", "flat"),
            "series":     scheme.get("series", "skylark250"),
        }
 
        if not validation["is_valid"]:
            all_valid = False
            invalid_schemes.append(scheme_key)
 
    results["all_valid"]       = all_valid
    results["invalid_schemes"] = invalid_schemes
    return results
 
 
def build_correction_prompt(original_request, design_json, validation_results):
    corrections = []
    scheme_names = {"scheme_a": "方案 A", "scheme_b": "方案 B", "scheme_c": "方案 C"}
    for scheme_key in validation_results.get("invalid_schemes", []):
        result = validation_results[scheme_key]
        errors = result["validation"].get("errors", [])
        error_text = "\n".join(f"  - [{e['rule_id']}] {e['message']}" for e in errors)
        corrections.append(f"**{scheme_names.get(scheme_key)}** 錯誤：\n{error_text}")
 
    return f"""你之前生成的設計方案有部分不符合 WikiHouse 官方製造規範，請修正後重新輸出。
 
原始需求：{original_request}
 
需要修正的方案：
{chr(10).join(corrections)}
 
修正規則：
- 開口 Block 數量不得超過牆板總數的 40%
- 每個方案必須包含 Floor Block
- 每個方案必須包含 Wall Block
- SK200 和 SK250 不能混用
- 方案 A 使用 S 跨距 Floor Block，方案 B 使用 M 跨距，方案 C 使用 M 跨距（山牆屋頂限制）
 
請修正 <DESIGN_JSON> 中有問題的方案，保持 span 和 roof 欄位不變。
"""
 
 
def validate_and_format_result(reply: str, all_blocks: list, original_request: str = "") -> dict:
    design_json = extract_design_json(reply)
 
    if not design_json:
        # 舊版文字解析（向後相容）
        block_map = {b["id"]: b for b in all_blocks}
        found = [b for bid, b in block_map.items() if bid in reply]
        stories = 2 if any(w in reply for w in ["兩層", "二層", "2層"]) else 1
        validation = validate_configuration(found, stories=stories) if found else {
            "is_valid": False, "errors": [], "warnings": [],
            "assembly_order": [], "summary": {}, "fabrication_notes": [], "ties": {}
        }
        return {
            "has_json":           False,
            "all_valid":          validation["is_valid"],
            "scheme_results":     {},
            "needs_correction":   False,
            "correction_prompt":  None,
            "recommended_blocks": found,
            "validation":         validation,
            "is_valid":           validation["is_valid"],
            "ties":               validation.get("ties", {}),
            "report":             format_validation_report(validation),
        }
 
    scheme_results = validate_all_schemes(design_json)
    all_valid = scheme_results["all_valid"]
 
    correction_prompt = None
    if not all_valid:
        correction_prompt = build_correction_prompt(original_request, design_json, scheme_results)
 
    best      = scheme_results.get("scheme_b", {})
    rep_blocks = best.get("blocks", [])
    rep_valid  = best.get("validation", {})
 
    return {
        "has_json":           True,
        "all_valid":          all_valid,
        "scheme_results":     scheme_results,
        "needs_correction":   not all_valid,
        "correction_prompt":  correction_prompt,
        "recommended_blocks": rep_blocks,
        "validation":         rep_valid,
        "is_valid":           all_valid,
        "ties":               rep_valid.get("ties", {}),
        "report":             format_validation_report(rep_valid) if rep_valid else "",
    }
 