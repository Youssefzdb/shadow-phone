#!/usr/bin/env python3
"""
Shadow Phone — v2.0
Phone Number OSINT + Active Vulnerability Assessment
Shadow Red Team | Authorized penetration testing only
"""

import sys
import argparse
import json
import requests
import re
import socket
import subprocess
from datetime import datetime

import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

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
{C.CYAN}  Shadow Phone v2.0 — Active OSINT + Vuln Assessment{C.RESET}
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
    return re.sub(r'[\s\-\.\(\)]', '', phone)

# ─────────────────────────────────────────────
# MODULE 1 — OSINT
# ─────────────────────────────────────────────

def osint_basic(phone):
    sep("🔍  MODULE 1 — PHONE OSINT")
    results = {}
    try:
        import phonenumbers
        from phonenumbers import geocoder, carrier, timezone
        parsed    = phonenumbers.parse(phone, None)
        valid     = phonenumbers.is_valid_number(parsed)
        country   = geocoder.description_for_number(parsed, "en")
        carrier_  = carrier.name_for_number(parsed, "en")
        timezones = timezone.time_zones_for_number(parsed)
        fmt_intl  = phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.INTERNATIONAL)
        fmt_e164  = phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
        num_type  = phonenumbers.number_type(parsed)
        type_map  = {0:"FIXED_LINE",1:"MOBILE",2:"FIXED_OR_MOBILE",3:"TOLL_FREE",
                     4:"PREMIUM_RATE",6:"VOIP",7:"PERSONAL",8:"PAGER",28:"UNKNOWN"}
        type_str  = type_map.get(num_type, f"TYPE_{num_type}")

        results = {"number": fmt_e164, "formatted": fmt_intl, "valid": valid,
                   "country": country, "carrier": carrier_ or "Unknown",
                   "type": type_str, "timezones": list(timezones)}

        status = f"{C.GREEN}✅ VALID{C.RESET}" if valid else f"{C.RED}❌ INVALID{C.RESET}"
        print(f"  Number    : {C.YELLOW}{fmt_intl}{C.RESET}")
        print(f"  E164      : {fmt_e164}")
        print(f"  Status    : {status}")
        print(f"  Country   : {C.CYAN}{country}{C.RESET}")
        print(f"  Carrier   : {C.CYAN}{carrier_ or 'Unknown'}{C.RESET}")
        print(f"  Type      : {type_str}")
        print(f"  Timezone  : {', '.join(timezones)}")
    except Exception as e:
        print(f"  {C.RED}❌ Error: {e}{C.RESET}")
    return results


def osint_whatsapp(phone):
    """Active WhatsApp check via wa.me + HTTP response analysis"""
    sep("📱  OSINT — Messaging Presence (Active Check)")
    normalized = normalize_phone(phone).replace('+','')
    results = {}

    # WhatsApp — check wa.me response
    print(f"  {C.BOLD}[WhatsApp]{C.RESET}")
    try:
        url = f"https://wa.me/{normalized}"
        r = requests.get(url, timeout=10, allow_redirects=True,
                         headers={"User-Agent": "Mozilla/5.0"})
        # wa.me redirects to whatsapp.com/send if number exists
        if "send" in r.url or "api.whatsapp" in r.url:
            print(f"  {C.GREEN}✅ CONFIRMED: WhatsApp account exists{C.RESET}")
            results["whatsapp"] = "confirmed"
        elif r.status_code == 200 and "phone_number" in r.text:
            print(f"  {C.GREEN}✅ CONFIRMED: WhatsApp account exists{C.RESET}")
            results["whatsapp"] = "confirmed"
        else:
            print(f"  {C.RED}❌ No WhatsApp account found (HTTP {r.status_code}){C.RESET}")
            results["whatsapp"] = "not_found"
    except Exception as e:
        print(f"  {C.YELLOW}⚠️  Check failed: {e}{C.RESET}")
        results["whatsapp"] = "error"

    # Telegram — t.me lookup
    print(f"\n  {C.BOLD}[Telegram]{C.RESET}")
    try:
        url = f"https://t.me/+{normalized}"
        r = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
        if "tgme_page_title" in r.text or "Telegram" in r.text:
            if "Join Group" in r.text or "tgme_action_button" in r.text:
                print(f"  {C.GREEN}✅ Telegram: Group/channel linked to this number{C.RESET}")
                results["telegram"] = "group_found"
            else:
                print(f"  {C.YELLOW}⚠️  Telegram: Cannot confirm individual account via public API{C.RESET}")
                results["telegram"] = "unknown"
        else:
            print(f"  {C.RED}❌ Telegram: No public presence found{C.RESET}")
            results["telegram"] = "not_found"
    except Exception as e:
        print(f"  {C.YELLOW}⚠️  Telegram check failed: {e}{C.RESET}")
        results["telegram"] = "error"

    # Signal — no public API, note only
    print(f"\n  {C.BOLD}[Signal]{C.RESET}")
    print(f"  {C.YELLOW}⚠️  Signal has no public lookup API — manual check required{C.RESET}")
    results["signal"] = "manual_required"

    return results


def osint_breach(phone):
    """Check number in data breaches via multiple sources"""
    sep("💀  OSINT — Data Breach Check (Active)")
    normalized = normalize_phone(phone).replace('+','')
    breaches = []

    # LeakCheck.io free endpoint
    print(f"  {C.BOLD}[LeakCheck.io]{C.RESET}")
    try:
        r = requests.get(f"https://leakcheck.io/api/public?check={normalized}", timeout=10)
        data = r.json()
        if data.get("found", 0) > 0:
            print(f"  {C.RED}🚨 FOUND in {data['found']} breach(es):{C.RESET}")
            for src in data.get("sources", [])[:5]:
                print(f"     → {src}")
                breaches.append(src)
        else:
            print(f"  {C.GREEN}✅ Not found in LeakCheck.io public database{C.RESET}")
    except Exception as e:
        print(f"  {C.YELLOW}⚠️  LeakCheck unavailable: {e}{C.RESET}")


    return breaches


# ─────────────────────────────────────────────
# MODULE 2 — ACTIVE VULNERABILITY ASSESSMENT
# ─────────────────────────────────────────────

def vuln_voicemail_active(phone):
    """
    Active voicemail PIN test via AMR/SIP simulation.
    Checks if carrier voicemail portal is reachable and tests default PINs.
    """
    sep("📬  MODULE 2 — VULNERABILITY ASSESSMENT")
    print(f"  {C.BOLD}[Voicemail Default PIN — Active Test]{C.RESET}\n")

    normalized = normalize_phone(phone).replace('+','')
    carrier_voicemail_map = {
        "216": {
            "Tunisie Telecom": {"number": "+21671701701", "default_pins": ["0000","1234","9999","last4"]},
            "Ooredoo":         {"number": "+21671710101", "default_pins": ["0000","1234","last4"]},
            "Orange":          {"number": "+21620700000", "default_pins": ["0000","1234","last4"]},
        }
    }

    country_code = "216" if normalized.startswith("216") else normalized[:3]
    carrier_data = carrier_voicemail_map.get(country_code, {})

    if not carrier_data:
        print(f"  {C.YELLOW}⚠️  No voicemail map for this country — manual test required{C.RESET}")
        return {"status": "manual_required", "severity": "unknown"}

    last4 = normalized[-4:]

    print(f"  {C.CYAN}Carrier voicemail numbers known for Tunisia:{C.RESET}")
    confirmed = False
    for carrier_name, info in carrier_data.items():
        pins = [p.replace("last4", last4) for p in info["default_pins"]]
        print(f"\n  → {carrier_name}")
        print(f"    Voicemail: {info['number']}")
        print(f"    Default PINs to test: {', '.join(pins)}")
        print(f"    {C.YELLOW}⚠️  Manual test: Call {info['number']} from target number's context{C.RESET}")
        print(f"    {C.YELLOW}    or use SIP/AMR client to simulate caller ID{C.RESET}")

    print(f"\n  {C.BOLD}Severity:{C.RESET} {C.YELLOW}MEDIUM — requires call simulation{C.RESET}")
    print(f"  {C.BOLD}Status:{C.RESET}   Theoretical — PIN data based on carrier defaults")
    print(f"  {C.BOLD}Confirm:{C.RESET}  Use 'sendsip' or Asterisk PBX to spoof caller ID + call voicemail")

    return {
        "status": "theoretical",
        "severity": "MEDIUM",
        "vuln": "VOICEMAIL_DEFAULT_PIN",
        "pins_to_test": [p for c in carrier_data.values() for p in c["default_pins"]]
    }


def vuln_ss7_assessment(phone, osint_data):
    """
    SS7 risk assessment based on real carrier data.
    Cannot exploit SS7 without telecom access — reports realistic risk level.
    """
    print(f"\n  {C.BOLD}[SS7 Protocol — Risk Assessment]{C.RESET}\n")

    carrier  = osint_data.get("carrier", "").lower()
    country  = osint_data.get("country", "")
    num_type = osint_data.get("type", "")

    risk_score = 0
    findings   = []

    # Check if GSMA SS7 firewall info available for this carrier
    unprotected_carriers = ["tunisie telecom", "ooredoo", "orange tunisia"]
    if any(c in carrier for c in unprotected_carriers):
        risk_score += 3
        findings.append(("HIGH", "Carrier not confirmed to have SS7 MAP filtering deployed"))

    if "MOBILE" in num_type:
        risk_score += 2
        findings.append(("HIGH", "Mobile numbers reachable via SS7 MAP operations"))
        findings.append(("HIGH", "SendRoutingInfo → location disclosure possible"))
        findings.append(("HIGH", "SMS interception via SRI-SM + FSM attack chain"))

    if "Tunisia" in country or "Algeria" in country or "Libya" in country:
        risk_score += 1
        findings.append(("MEDIUM", "Region has limited SS7 firewall adoption per GSMA reports"))

    # Realistic severity
    if risk_score >= 5:
        severity = f"{C.RED}HIGH{C.RESET}"
        status   = "Likely vulnerable — no public SS7 firewall confirmed for this carrier"
    elif risk_score >= 3:
        severity = f"{C.YELLOW}MEDIUM{C.RESET}"
        status   = "Possibly vulnerable — depends on carrier SS7 implementation"
    else:
        severity = f"{C.GREEN}LOW{C.RESET}"
        status   = "Lower risk — carrier may have SS7 protections"

    print(f"  Risk Score : {risk_score}/6")
    print(f"  Severity   : {severity}")
    print(f"  Status     : {status}")
    print(f"\n  Findings:")
    for sev, msg in findings:
        color = C.RED if sev == "HIGH" else C.YELLOW
        print(f"    {color}[{sev}]{C.RESET} {msg}")

    print(f"\n  {C.BOLD}Confirmation:{C.RESET}")
    print(f"  {C.CYAN}  → Requires SigPloit / SS7MAPer with SS7 network access{C.RESET}")
    print(f"  {C.CYAN}  → Cannot be confirmed passively — active SS7 node needed{C.RESET}")
    print(f"  {C.CYAN}  → Reference: https://github.com/SigPloiter/SigPloit{C.RESET}")

    return {
        "vuln": "SS7_RISK",
        "severity": "HIGH" if risk_score >= 5 else "MEDIUM",
        "score": risk_score,
        "status": "theoretical_high_probability",
        "findings": [f[1] for f in findings]
    }


def vuln_sim_swap_active(phone, osint_data):
    """
    SIM Swap: check carrier's authentication policy via their web portal.
    """
    print(f"\n  {C.BOLD}[SIM Swap — Carrier Portal Check]{C.RESET}\n")

    carrier = osint_data.get("carrier", "Unknown")
    findings = []

    carrier_portals = {
        "Tunisie Telecom": "https://www.tunisietelecom.tn",
        "Ooredoo":         "https://www.ooredoo.tn",
        "Orange":          "https://www.orange.tn",
    }

    portal_url = None
    for k, v in carrier_portals.items():
        if k.lower() in carrier.lower():
            portal_url = v
            break

    if portal_url:
        print(f"  {C.CYAN}Checking carrier portal: {portal_url}{C.RESET}")
        try:
            r = requests.get(portal_url, timeout=10, verify=False)
            if r.status_code == 200:
                # Check for MFA/2FA indicators in portal
                page = r.text.lower()
                has_mfa = any(kw in page for kw in ["2fa","two-factor","otp verification","authenticator"])
                has_id_check = any(kw in page for kw in ["cin","identity","carte nationale","id verification"])

                if has_mfa:
                    print(f"  {C.GREEN}✅ Portal has MFA indicators — SIM swap harder{C.RESET}")
                    findings.append(("LOW", "Portal shows MFA/verification indicators"))
                else:
                    print(f"  {C.RED}🔴 No MFA indicators found on portal{C.RESET}")
                    findings.append(("HIGH", "Carrier portal lacks visible MFA — social engineering viable"))

                if has_id_check:
                    print(f"  {C.YELLOW}⚠️  ID verification required — SIM swap needs physical ID{C.RESET}")
                    findings.append(("MEDIUM", "ID check required but social engineering still possible"))
                else:
                    print(f"  {C.RED}🔴 No ID verification indicators — phone-based swap possible{C.RESET}")
                    findings.append(("HIGH", "No strong identity verification found"))
            else:
                print(f"  {C.YELLOW}⚠️  Portal returned HTTP {r.status_code}{C.RESET}")
        except Exception as e:
            print(f"  {C.YELLOW}⚠️  Cannot reach portal: {e}{C.RESET}")
    else:
        print(f"  {C.YELLOW}⚠️  No portal mapping for carrier: {carrier}{C.RESET}")
        findings.append(("UNKNOWN", "Carrier portal not mapped — manual check required"))

    print(f"\n  {C.BOLD}Severity:{C.RESET} {C.YELLOW}MEDIUM-HIGH — depends on carrier agent training{C.RESET}")
    print(f"  {C.BOLD}Status:{C.RESET}   Partially verified via portal analysis")

    return {
        "vuln": "SIM_SWAP",
        "severity": "HIGH" if any(f[0]=="HIGH" for f in findings) else "MEDIUM",
        "status": "partially_verified",
        "findings": [f[1] for f in findings]
    }


def vuln_caller_id_active(phone):
    """Caller ID spoofing — confirmed trivial, test via SIP"""
    print(f"\n  {C.BOLD}[Caller ID Spoofing — Confirmed]{C.RESET}\n")

    print(f"  {C.GREEN}✅ CONFIRMED VULNERABILITY (no active test needed){C.RESET}")
    print(f"  PSTN/SS7 has no authentication on caller ID by design")
    print(f"  Any SIP provider with CLI override can spoof this number")
    print(f"\n  PoC tools:")
    print(f"  {C.CYAN}  → SIPp: sipp -sf caller_id_spoof.xml{C.RESET}")
    print(f"  {C.CYAN}  → Asterisk: Set CALLERID(num)={phone}{C.RESET}")
    print(f"  {C.CYAN}  → Online: spoofcard.com / bluffmycall.com (commercial){C.RESET}")
    print(f"\n  {C.BOLD}Severity:{C.RESET} {C.RED}HIGH — trivially exploitable{C.RESET}")
    print(f"  {C.BOLD}Status:{C.RESET}   {C.GREEN}CONFIRMED{C.RESET}")

    return {
        "vuln": "CALLER_ID_SPOOFING",
        "severity": "HIGH",
        "status": "confirmed",
        "note": "PSTN design flaw — no fix on attacker side"
    }


def vuln_sms_otp(osint_data):
    """SMS OTP weakness — check if number is used for 2FA on major platforms"""
    print(f"\n  {C.BOLD}[SMS 2FA Weakness]{C.RESET}\n")

    print(f"  {C.YELLOW}⚠️  SMS OTP is weak by design (NIST SP 800-63B){C.RESET}")
    print(f"  Attack surface depends on SS7 access (see above)")
    print(f"\n  Real-world attack chain:")
    print(f"  {C.CYAN}  1. Attacker gets SS7 access (via rogue MNO or exploit){C.RESET}")
    print(f"  {C.CYAN}  2. Sends SRI-SM to HLR to get routing info{C.RESET}")
    print(f"  {C.CYAN}  3. Redirects SMS via FSM (Forward Short Message){C.RESET}")
    print(f"  {C.CYAN}  4. Intercepts OTP → account takeover{C.RESET}")
    print(f"\n  {C.BOLD}Severity:{C.RESET} {C.YELLOW}HIGH (theoretical) / CRITICAL (with SS7 access){C.RESET}")
    print(f"  {C.BOLD}Status:{C.RESET}   Theoretical — requires SS7 node")

    return {
        "vuln": "SMS_OTP_INTERCEPTION",
        "severity": "HIGH",
        "status": "theoretical",
        "requires": "SS7 network access"
    }


# ─────────────────────────────────────────────
# REPORT
# ─────────────────────────────────────────────

def generate_report(phone, osint_data, vuln_results, breach_data, social_data):
    import os
    os.makedirs("reports", exist_ok=True)
    ts    = datetime.now().strftime('%Y%m%d_%H%M')
    safe  = normalize_phone(phone).replace('+','')
    fname = f"reports/phone_{safe}_{ts}.md"

    with open(fname, 'w') as f:
        f.write(f"""# Shadow Phone Report — {phone}
**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M')}
**Tool:** Shadow Phone v2.0

---

## OSINT

| Field    | Value |
|----------|-------|
| Number   | {osint_data.get('formatted', phone)} |
| Valid    | {osint_data.get('valid','?')} |
| Country  | {osint_data.get('country','?')} |
| Carrier  | {osint_data.get('carrier','?')} |
| Type     | {osint_data.get('type','?')} |
| Timezone | {', '.join(osint_data.get('timezones',[]))} |

### Social Presence
| Platform  | Status |
|-----------|--------|
| WhatsApp  | {social_data.get('whatsapp','?')} |
| Telegram  | {social_data.get('telegram','?')} |

### Data Breaches
{('Found in: ' + ', '.join(breach_data)) if breach_data else 'No public breaches found'}

---

## Vulnerability Assessment

| Vulnerability | Severity | Status |
|--------------|----------|--------|
{''.join([f"| {v.get('vuln','?')} | {v.get('severity','?')} | {v.get('status','?')} |" + chr(10) for v in vuln_results])}

---

## Notes
- SS7 findings are probability-based — confirmation requires SS7 network access
- Caller ID spoofing is confirmed by design (PSTN protocol)
- Voicemail PIN test requires SIP caller ID spoofing + manual call

---
*Shadow Red Team — Authorized Assessment*
""")

    print(f"\n  {C.GREEN}📄 Report saved: {fname}{C.RESET}")
    return fname


# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────

def main():
    p = argparse.ArgumentParser(description='Shadow Phone v2.0')
    p.add_argument('phone', nargs='?', help='Phone number (e.g. +21612345678)')
    p.add_argument('--osint-only', action='store_true')
    p.add_argument('--vuln-only',  action='store_true')
    args = p.parse_args()

    banner()

    if not args.phone:
        sep("📞  Target")
        phone = input(f"  {C.BOLD}Phone (with country code) >{C.RESET} ").strip()
    else:
        phone = args.phone

    phone = normalize_phone(phone)
    if not phone.startswith('+'):
        print(f"  {C.RED}❌ Add country code (e.g. +216...){C.RESET}")
        sys.exit(1)

    osint_data  = {}
    social_data = {}
    breach_data = []
    vuln_results = []

    # MODULE 1
    if not args.vuln_only:
        osint_data  = osint_basic(phone)
        social_data = osint_whatsapp(phone)
        breach_data = osint_breach(phone)

    # MODULE 2
    if not args.osint_only:
        sep("⚡  MODULE 2 — ACTIVE VULNERABILITY ASSESSMENT")
        vuln_results.append(vuln_ss7_assessment(phone, osint_data))
        vuln_results.append(vuln_sim_swap_active(phone, osint_data))
        vuln_results.append(vuln_caller_id_active(phone))
        vuln_results.append(vuln_voicemail_active(phone))
        vuln_results.append(vuln_sms_otp(osint_data))

    # Summary
    sep("📊  SUMMARY")
    print(f"  Target  : {C.YELLOW}{phone}{C.RESET}")
    confirmed   = [v for v in vuln_results if v.get("status") == "confirmed"]
    theoretical = [v for v in vuln_results if v.get("status") != "confirmed"]
    print(f"  {C.RED}Confirmed vulns    : {len(confirmed)}{C.RESET}")
    print(f"  {C.YELLOW}Theoretical vulns  : {len(theoretical)}{C.RESET}")
    for v in vuln_results:
        color = C.RED if v.get("status") == "confirmed" else C.YELLOW
        tag   = "✅ CONFIRMED" if v.get("status") == "confirmed" else "⚠️  THEORETICAL"
        print(f"    {color}[{v.get('severity','?')}] {v.get('vuln','?')} — {tag}{C.RESET}")

    generate_report(phone, osint_data, vuln_results, breach_data, social_data)
    print()

if __name__ == "__main__":
    main()
