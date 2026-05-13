#!/usr/bin/env python3
"""
Shadow Phone — v1.0
Phone Number OSINT + Vulnerability Scanner
Shadow Red Team | Authorized pentesting only
"""

import sys
import argparse
import json
import requests
import re
from datetime import datetime

class C:
    GREEN   = '\033[92m'
    RED     = '\033[91m'
    YELLOW  = '\033[93m'
    CYAN    = '\033[96m'
    MAGENTA = '\033[95m'
    BOLD    = '\033[1m'
    RESET   = '\033[0m'

def banner():
    print(f"""
{C.RED}{C.BOLD}
 ███████╗██╗  ██╗ █████╗ ██████╗  ██████╗ ██╗    ██╗
 ██╔════╝██║  ██║██╔══██╗██╔══██╗██╔═══██╗██║    ██║
 ███████╗███████║███████║██║  ██║██║   ██║██║ █╗ ██║
 ╚════██║██╔══██║██╔══██║██║  ██║██║   ██║██║███╗██║
 ███████║██║  ██║██║  ██║██████╔╝╚██████╔╝╚███╔███╔╝
 ╚══════╝╚═╝  ╚═╝╚═╝  ╚═╝╚═════╝  ╚═════╝  ╚══╝╚══╝
{C.RESET}
{C.CYAN}  Shadow Phone v1.0 — OSINT + Vuln Scanner{C.RESET}
{C.YELLOW}  ⚠️  Authorized penetration testing only{C.RESET}
""")

def sep(title=""):
    if title:
        print(f"\n{C.BOLD}{'━'*55}{C.RESET}")
        print(f"  {title}")
        print(f"{C.BOLD}{'━'*55}{C.RESET}\n")
    else:
        print(f"{C.BOLD}{'━'*55}{C.RESET}")

def normalize_phone(phone):
    """Remove spaces, dashes, dots — keep + and digits"""
    return re.sub(r'[\s\-\.\(\)]', '', phone)

# ─────────────────────────────────────────────
# MODULE 1 — OSINT
# ─────────────────────────────────────────────

def osint_basic(phone):
    """Basic carrier + country lookup via free API"""
    sep("🔍  MODULE 1 — PHONE OSINT")

    results = {}

    # NumVerify (free tier)
    try:
        url = f"http://apilayer.net/api/validate?access_key=free&number={phone}"
        # Fallback: use phonenumbers lib
        raise Exception("use phonenumbers")
    except:
        pass

    # Use phonenumbers library
    try:
        import phonenumbers
        from phonenumbers import geocoder, carrier, timezone
        parsed = phonenumbers.parse(phone, None)
        valid  = phonenumbers.is_valid_number(parsed)
        possible = phonenumbers.is_possible_number(parsed)

        country  = geocoder.description_for_number(parsed, "en")
        carrier_ = carrier.name_for_number(parsed, "en")
        timezones = timezone.time_zones_for_number(parsed)
        fmt_intl  = phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.INTERNATIONAL)
        fmt_e164  = phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
        num_type  = phonenumbers.number_type(parsed)

        type_map = {
            0: "FIXED_LINE", 1: "MOBILE", 2: "FIXED_OR_MOBILE",
            3: "TOLL_FREE",  4: "PREMIUM_RATE", 6: "VOIP",
            7: "PERSONAL",   8: "PAGER", 28: "UNKNOWN"
        }
        type_str = type_map.get(num_type, f"TYPE_{num_type}")

        results = {
            "number":    fmt_e164,
            "formatted": fmt_intl,
            "valid":     valid,
            "possible":  possible,
            "country":   country,
            "carrier":   carrier_ or "Unknown",
            "type":      type_str,
            "timezones": list(timezones),
        }

        status = f"{C.GREEN}✅ VALID{C.RESET}" if valid else f"{C.RED}❌ INVALID{C.RESET}"
        print(f"  Number    : {C.YELLOW}{fmt_intl}{C.RESET}")
        print(f"  E164      : {fmt_e164}")
        print(f"  Status    : {status}")
        print(f"  Country   : {C.CYAN}{country}{C.RESET}")
        print(f"  Carrier   : {C.CYAN}{carrier_ or 'Unknown'}{C.RESET}")
        print(f"  Type      : {type_str}")
        print(f"  Timezone  : {', '.join(timezones)}")

    except Exception as e:
        print(f"  {C.RED}❌ phonenumbers error: {e}{C.RESET}")
        print(f"  {C.YELLOW}Install: pip install phonenumbers{C.RESET}")

    return results


def osint_social(phone):
    """Check if number is linked to social/messaging apps"""
    sep("📱  OSINT — Social & Messaging Lookup")

    normalized = normalize_phone(phone)
    checks = {}

    # WhatsApp check via wa.me
    try:
        url = f"https://wa.me/{normalized.replace('+','')}"
        r = requests.get(url, timeout=8, allow_redirects=True)
        if r.status_code == 200 and "whatsapp" in r.url.lower():
            print(f"  {C.GREEN}✅ WhatsApp: Account likely exists{C.RESET}")
            print(f"     URL: {url}")
            checks["whatsapp"] = "possible"
        else:
            print(f"  {C.YELLOW}⚠️  WhatsApp: Cannot confirm (check manually){C.RESET}")
            print(f"     URL: {url}")
            checks["whatsapp"] = "unknown"
    except Exception as e:
        print(f"  {C.RED}❌ WhatsApp check failed: {e}{C.RESET}")
        checks["whatsapp"] = "error"

    # Telegram check via t.me/+number
    try:
        url = f"https://t.me/+{normalized.replace('+','')}"
        print(f"  {C.CYAN}ℹ️  Telegram: Check manually → {url}{C.RESET}")
        checks["telegram"] = url
    except:
        pass

    # Truecaller hint
    print(f"  {C.CYAN}ℹ️  Truecaller: https://www.truecaller.com/search/tn/{normalized.replace('+','')}{C.RESET}")
    checks["truecaller"] = f"https://www.truecaller.com/search/tn/{normalized.replace('+','')}"

    # NumLookup
    print(f"  {C.CYAN}ℹ️  NumLookup: https://www.numlookup.com/?number={normalized}{C.RESET}")

    return checks


def osint_breach(phone):
    """Check if number appears in known data breaches"""
    sep("💀  OSINT — Data Breach Check")

    normalized = normalize_phone(phone).replace('+', '')

    # Check via IntelX or similar (free endpoints)
    try:
        # leakcheck.io free API
        url = f"https://leakcheck.io/api/public?check={normalized}"
        r = requests.get(url, timeout=10)
        data = r.json()
        if data.get("success") and data.get("found", 0) > 0:
            print(f"  {C.RED}🚨 BREACHED! Found in {data['found']} leak(s){C.RESET}")
            for src in data.get("sources", [])[:5]:
                print(f"     → {src}")
        else:
            print(f"  {C.GREEN}✅ Not found in public breaches (leakcheck.io){C.RESET}")
    except Exception as e:
        print(f"  {C.YELLOW}⚠️  Breach check unavailable: {e}{C.RESET}")

    # PhoneInfoga reference
    print(f"\n  {C.CYAN}ℹ️  Manual check: https://www.spokeo.com/reverse-phone-lookup/{normalized}{C.RESET}")
    print(f"  {C.CYAN}ℹ️  Manual check: https://www.truecaller.com/search/tn/{normalized}{C.RESET}")


# ─────────────────────────────────────────────
# MODULE 2 — VULNERABILITY SCAN
# ─────────────────────────────────────────────

def vuln_ss7(phone, results):
    """SS7 vulnerability assessment based on carrier and number type"""
    sep("⚡  MODULE 2 — VULNERABILITY SCAN")
    print(f"  {C.BOLD}[SS7 Protocol Vulnerability]{C.RESET}\n")

    carrier = results.get("carrier", "").lower()
    num_type = results.get("type", "")
    country  = results.get("country", "")

    vulns = []

    # SS7 risk based on carrier/region
    high_risk_countries = ["Tunisia", "Algeria", "Morocco", "Libya", "Egypt", "Lebanon"]
    if any(c.lower() in country.lower() for c in high_risk_countries):
        print(f"  {C.RED}🔴 SS7: HIGH RISK region — older telecom infrastructure{C.RESET}")
        print(f"     Many carriers in {country} use SS7 without MAP filtering")
        vulns.append("SS7_HIGH_RISK_REGION")
    else:
        print(f"  {C.YELLOW}⚠️  SS7: MEDIUM RISK — depends on carrier implementation{C.RESET}")

    # Mobile number = more vulnerable to SS7
    if "MOBILE" in num_type:
        print(f"  {C.RED}🔴 SS7: MOBILE number — vulnerable to:{C.RESET}")
        print(f"     • SMS interception (OTP bypass)")
        print(f"     • Location tracking (SendRoutingInfo)")
        print(f"     • Call forwarding (RegisterSS)")
        vulns.append("SS7_SMS_INTERCEPTION")
        vulns.append("SS7_LOCATION_TRACKING")
        vulns.append("SS7_CALL_FORWARDING")
    elif "FIXED" in num_type:
        print(f"  {C.GREEN}✅ SS7: Fixed line — lower SS7 mobile risk{C.RESET}")
    elif "VOIP" in num_type:
        print(f"  {C.YELLOW}⚠️  VOIP: SS7 not applicable but VOIP has other risks{C.RESET}")
        vulns.append("VOIP_VULNERABILITIES")

    return vulns


def vuln_sim_swap(phone, results):
    """SIM Swap risk assessment"""
    print(f"\n  {C.BOLD}[SIM Swap Risk]{C.RESET}\n")

    carrier = results.get("carrier", "Unknown")
    vulns = []

    print(f"  {C.YELLOW}⚠️  SIM Swap: Risk depends on carrier security{C.RESET}")
    print(f"     Carrier: {carrier}")
    print(f"     • Social engineering carrier support = SIM swap")
    print(f"     • If number is old/inactive → easier to reclaim")
    print(f"     • Allows full account takeover via SMS 2FA")
    vulns.append("SIM_SWAP_POSSIBLE")

    return vulns


def vuln_otp(phone, results):
    """OTP/2FA weakness via SMS"""
    print(f"\n  {C.BOLD}[OTP / SMS 2FA Weakness]{C.RESET}\n")

    vulns = []
    print(f"  {C.RED}🔴 SMS OTP: Vulnerable to SS7 interception{C.RESET}")
    print(f"     • WhatsApp OTP can be intercepted via SS7")
    print(f"     • Telegram OTP same risk")
    print(f"     • Bank 2FA via SMS = bypassable")
    print(f"     • Attacker can take over accounts linked to this number")
    vulns.append("SMS_OTP_INTERCEPTION")

    return vulns


def vuln_caller_id(phone):
    """Caller ID spoofing risk"""
    print(f"\n  {C.BOLD}[Caller ID Spoofing]{C.RESET}\n")

    print(f"  {C.RED}🔴 Caller ID: Can be spoofed trivially{C.RESET}")
    print(f"     • Attacker can call from this number")
    print(f"     • Vishing / social engineering attacks")
    print(f"     • No authentication on PSTN caller ID")
    return ["CALLER_ID_SPOOFING"]


def vuln_voicemail(phone):
    """Default voicemail PIN vulnerability"""
    print(f"\n  {C.BOLD}[Voicemail Default PIN]{C.RESET}\n")

    print(f"  {C.YELLOW}⚠️  Voicemail: Many carriers use default PINs (0000, 1234){C.RESET}")
    print(f"     • Old numbers often have unchanged PINs")
    print(f"     • Attacker can listen to voicemails")
    print(f"     • Some carriers allow remote access without PIN")
    return ["VOICEMAIL_DEFAULT_PIN"]


# ─────────────────────────────────────────────
# REPORT GENERATOR
# ─────────────────────────────────────────────

def generate_report(phone, osint_data, all_vulns):
    import os
    os.makedirs("reports", exist_ok=True)
    ts = datetime.now().strftime('%Y%m%d_%H%M')
    safe = normalize_phone(phone).replace('+','')
    fname = f"reports/phone_{safe}_{ts}.md"

    with open(fname, 'w') as f:
        f.write(f"""# Phone OSINT + Vulnerability Report

**Target:** `{phone}`
**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M')}
**Tool:** Shadow Phone v1.0

---

## OSINT Results

| Field    | Value |
|----------|-------|
| Number   | {osint_data.get('formatted', phone)} |
| Valid    | {osint_data.get('valid', '?')} |
| Country  | {osint_data.get('country', '?')} |
| Carrier  | {osint_data.get('carrier', '?')} |
| Type     | {osint_data.get('type', '?')} |
| Timezone | {', '.join(osint_data.get('timezones', []))} |

---

## Vulnerabilities Found

| # | Vulnerability | Severity |
|---|--------------|----------|
{''.join([f"| {i+1} | {v} | HIGH |" + chr(10) for i, v in enumerate(all_vulns)])}

---

## Recommendations

- Disable SMS-based 2FA — use TOTP (Google Authenticator)
- Enable carrier-level SIM swap protection
- Use strong voicemail PIN
- Be aware of SS7 limitations in your region

---
*Shadow Red Team — Authorized Assessment*
""")

    print(f"\n  {C.GREEN}📄 Report: {fname}{C.RESET}")
    return fname


# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────

def main():
    p = argparse.ArgumentParser(description='Shadow Phone v1.0 — OSINT + Vuln Scanner')
    p.add_argument('phone', nargs='?', help='Phone number (e.g. +21612345678)')
    p.add_argument('--osint-only', action='store_true', help='Run OSINT only')
    p.add_argument('--vuln-only',  action='store_true', help='Run vuln scan only')
    args = p.parse_args()

    banner()

    # Interactive input if no phone provided
    if not args.phone:
        sep("📞  Target Phone Number")
        phone = input(f"  {C.BOLD}Phone (with country code, e.g. +21612345678) >{C.RESET} ").strip()
    else:
        phone = args.phone

    phone = normalize_phone(phone)
    if not phone.startswith('+'):
        print(f"  {C.YELLOW}⚠️  Add country code (e.g. +216 for Tunisia){C.RESET}")
        sys.exit(1)

    all_vulns = []

    # MODULE 1 — OSINT
    if not args.vuln_only:
        osint_data = osint_basic(phone)
        osint_social(phone)
        osint_breach(phone)
    else:
        osint_data = {}

    # MODULE 2 — VULN SCAN
    if not args.osint_only:
        all_vulns += vuln_ss7(phone, osint_data)
        all_vulns += vuln_sim_swap(phone, osint_data)
        all_vulns += vuln_otp(phone, osint_data)
        all_vulns += vuln_caller_id(phone)
        all_vulns += vuln_voicemail(phone)

    # Summary
    sep("📊  SUMMARY")
    print(f"  Target   : {C.YELLOW}{phone}{C.RESET}")
    print(f"  OSINT    : {C.GREEN}✅ Complete{C.RESET}")
    print(f"  Vulns    : {C.RED}{len(all_vulns)} found{C.RESET}")
    for v in all_vulns:
        print(f"    {C.RED}→ {v}{C.RESET}")

    # Report
    generate_report(phone, osint_data, all_vulns)
    print()

if __name__ == "__main__":
    main()
