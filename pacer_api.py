# link to API Guide: https://pacer.uscourts.gov/sites/default/files/files/PCL-API-Document_4.pdf

import requests
from typing import Dict, Any, Optional

# ===== Choose environment: "QA" or "PROD" =====
ENV = "PROD"   # change to "PROD" when you’re ready

# ===== Credentials =====
USERNAME = "provendataforensics"
QA_PASSWORD = "Yirshovi1!Yirshovi1!"
PROD_PASSWORD = "Yirshovi1!"

# ===== PACER PCL API endpoints =====
CONFIG = {
    "QA": {
        "AUTH_URL": "https://qa-login.uscourts.gov/services/cso-auth",
        "PCL_API_ROOT": "https://qa-pcl.uscourts.gov/pcl-public-api/rest",
        "PASSWORD": QA_PASSWORD,
    },
    "PROD": {
        "AUTH_URL": "https://pacer.login.uscourts.gov/services/cso-auth",
        "PCL_API_ROOT": "https://pcl.uscourts.gov/pcl-public-api/rest",
        "PASSWORD": PROD_PASSWORD,
    },
}

def env_cfg(env: str) -> Dict[str, str]:
    if env not in CONFIG:
        raise ValueError("ENV must be 'QA' or 'PROD'")
    return CONFIG[env]

def authenticate(username: str, password: str, auth_url: str) -> Optional[str]:
    print(f"🔐 Authenticating to {ENV}...")
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    payload = {"loginId": username, "password": password}

    r = requests.post(auth_url, headers=headers, json=payload, allow_redirects=False)
    print("📄 Raw Response:", r.status_code)
    try:
        j = r.json()
    except Exception:
        j = {"_raw": r.text}
    print("📦 Auth JSON response:", j)
    r.raise_for_status()

    token = j.get("nextGenCSO")
    if not token:
        print("❌ No token received. Login failed.")
        return None
    print("✅ Auth successful.")
    return token

def search_cases_by_date(token: str, api_root: str, page: int = 0) -> None:
    if not token:
        print("⚠️ No token available, skipping case search.")
        return

    print("📅 Performing case search for dateFiledFrom...")

    url = f"{api_root}/cases/find?page={page}"
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "X-NEXT-GEN-CSO": token,
    }

    # In QA this payload return 1 case
    # payload = {
    #     "caseTitle": "Popkin",    
    #     "dateFiledFrom": "2000-08-01",
    #     "caseStatus": "O",
    # }
    
    payload = {
        "dateFiledFrom": "2025-08-01",
        "caseStatus": "O",
    }

    print("📤 Payload sent:", payload)
    r = requests.post(url, headers=headers, json=payload)
    print("📬 Response body:", r.text)

    if r.status_code != 200:
        print(f"❌ ERROR {r.status_code}: {r.reason}")
        return

    data: Dict[str, Any] = r.json()

    # Show receipt (PROD will include billable pages)
    if "receipt" in data:
        receipt = data["receipt"]
        print(f"🧾 Receipt: fee={receipt.get('searchFee')} pages={receipt.get('billablePages')}")

    # Results can appear as "content" (pageable) or "cases" (older shape in some examples)
    cases = data.get("content") or data.get("cases") or []

    # Totals (handle both shapes)
    total = (
        data.get("pageInfo", {}).get("totalElements")
        if data.get("pageInfo")
        else data.get("totalCount", len(cases))
    )

    print(f"✅ Found {total} cases (showing up to 5):")
    for case in cases[:1]:
        print(case)

if __name__ == "__main__":
    cfg = env_cfg(ENV)
    token = authenticate(USERNAME, cfg["PASSWORD"], cfg["AUTH_URL"])
    search_cases_by_date(token, cfg["PCL_API_ROOT"])
