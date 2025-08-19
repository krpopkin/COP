# link to API Guide: https://pacer.uscourts.gov/sites/default/files/files/PCL-API-Document_4.pdf

import requests
from typing import Dict, Any, Optional, List
from db import get_conn

# ===== Choose environment: "QA" or "PROD" =====
ENV = "PROD"   # change to "PROD" when you're ready

# ===== Credentials =====
QA_USERNAME = 'krpopkin'
QA_PASSWORD = "Reallystupid1!"

PROD_USERNAME = "provendataforensics"
PROD_PASSWORD = "Yirshovi1!"

# ===== PACER PCL API endpoints =====
CONFIG = {
    "QA": {
        "AUTH_URL": "https://qa-login.uscourts.gov/services/cso-auth",
        "PCL_API_ROOT": "https://qa-pcl.uscourts.gov/pcl-public-api/rest",
        "USERNAME": QA_USERNAME,
        "PASSWORD": QA_PASSWORD,
    },
    "PROD": {
        "AUTH_URL": "https://pacer.login.uscourts.gov/services/cso-auth",
        "PCL_API_ROOT": "https://pcl.uscourts.gov/pcl-public-api/rest",
        "USERNAME": PROD_USERNAME,
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

def get_court_id_from_region(region: str) -> Optional[str]:
    """Look up court_id from the court_ids table based on region name."""
    if not region or region == "All":
        return None
    
    conn = get_conn()
    try:
        cur = conn.execute("SELECT court_id FROM court_ids WHERE region = %s", (region,))
        result = cur.fetchone()
        return result['court_id'] if result else None
    finally:
        conn.close()

def search_cases_by_date(token: str, api_root: str, date_from: str, date_to: str = None, region: str = None, page: int = 0) -> List[Dict[str, Any]]:
    if not token:
        print("⚠️ No token available, skipping case search.")
        return []

    print("📅 Performing case search with date range and filters...")
    url = f"{api_root}/cases/find?page={page}"
    headers = {"Content-Type": "application/json", "Accept": "application/json", "X-NEXT-GEN-CSO": token}
    
    # Old payload (commented out)
    # payload = {"caseTitle": "Smith", "dateFiledFrom": date_from}
    
    # Look up court_id from region
    court_id = get_court_id_from_region(region)
    
    # New payload with dateFrom, dateTo, region, jurisdiction type, and case status
    print('***********************  MY PRINT STATEMENTS *************************')
    print(f'Date from:', date_from)
    print(f'Date to:', date_to)
    print(f'region in:', region)
    payload = {
        "dateFiledFrom": date_from,
        "dateFiledTo": date_to,
        "jurisdictionType": "cr",  # "cr" for criminal cases
        "caseStatus": "O"  # "O" for open cases, "C" for closed cases
    }
    
    # Add court_id if we found one for the region
    if court_id:
        payload["courtId"] = [court_id]  # courtId expects a list

    print('court id:', court_id)

    print("📤 Payload sent:", payload)
    r = requests.post(url, headers=headers, json=payload)
    print("📬 Response body:", r.text)

    if r.status_code != 200:
        print(f"❌ ERROR {r.status_code}: {r.reason}")
        return []

    data: Dict[str, Any] = r.json()
    if "receipt" in data:
        rcpt = data["receipt"]
        print(f"🧾 Receipt: fee={rcpt.get('searchFee')} pages={rcpt.get('billablePages')}")

    cases = data.get("content") or data.get("cases") or []
    print(f"✅ Found {data.get('pageInfo', {}).get('totalElements', len(cases))} cases (showing all).")
    # for c in cases:
    #     print(c)
    return cases

def upsert_pacer_cases(cases: List[Dict[str, Any]]) -> int:
    """
    Insert new cases and update existing ones (matched on case_id).
    Returns the total number of rows affected (inserted + updated).
    """
    if not cases:
        return 0

    inserted = 0
    updated = 0

    for c in cases:
        case_id = c.get("caseId")
        if case_id is None:
            # Skip rows without a caseId (cannot match/update deterministically)
            continue

        cn = c.get("caseNumber")
        cn_str = str(cn) if cn is not None else None

        case_summary_url = (
            f"https://ecf.casd.uscourts.gov/cgi-bin/qrySummary.pl?{cn_str}"
            if cn_str else None
        )
        parties_url = (
            f"https://ecf.casd.uscourts.gov/cgi-bin/qryParties.pl?{cn_str}"
            if cn_str else None
        )
        attorney_url = (
            f"https://ecf.casd.uscourts.gov/cgi-bin/qryAttorneys.pl?{cn_str}"
            if cn_str else None
        )

        # Get fresh connection for each case to avoid prepared statement conflicts
        conn = get_conn()
        try:
            with conn.cursor() as cur:
                # 1) Try UPDATE first (match on case_id)
                cur.execute(
                    """
                    UPDATE pacer_cases
                       SET court_id = %s,
                           case_number = %s,
                           case_type = %s,
                           case_title = %s,
                           date_filed = %s,
                           jurisdiction_type = %s,
                           case_link = %s,
                           case_summary = %s,
                           parties = %s,
                           attorney = %s
                     WHERE case_id = %s
                    """,
                    (
                        c.get("courtId"),
                        c.get("caseNumber"),
                        c.get("caseType"),
                        c.get("caseTitle"),
                        c.get("dateFiled"),
                        c.get("jurisdictionType"),
                        c.get("caseLink"),
                        case_summary_url,
                        parties_url,
                        attorney_url,
                        case_id,
                    ),
                )

                if cur.rowcount and cur.rowcount > 0:
                    updated += cur.rowcount
                else:
                    # 2) If no row was updated, INSERT a new one
                    cur.execute(
                        """
                        INSERT INTO pacer_cases (
                            court_id, case_id, case_number, case_type, case_title, date_filed,
                            jurisdiction_type, case_link, case_summary, parties, attorney
                        ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                        """,
                        (
                            c.get("courtId"),
                            case_id,
                            c.get("caseNumber"),
                            c.get("caseType"),
                            c.get("caseTitle"),
                            c.get("dateFiled"),
                            c.get("jurisdictionType"),
                            c.get("caseLink"),
                            case_summary_url,
                            parties_url,
                            attorney_url,
                        ),
                    )
                    inserted += 1
            
            conn.commit()
        finally:
            conn.close()

    print(f"💾 Upsert complete: inserted={inserted}, updated={updated}")
    return inserted + updated

if __name__ == "__main__":
    cfg = env_cfg(ENV)
    token = authenticate(cfg["USERNAME"], cfg["PASSWORD"], cfg["AUTH_URL"])
    cases = search_cases_by_date(token, cfg["PCL_API_ROOT"], "2024-01-01")
    
    n = upsert_pacer_cases(cases)
    print(f"💾 Upserted {n} row(s) into pacer_cases.")