# Shadow Phone 📱

**Phone Number OSINT + Vulnerability Scanner**
Shadow Red Team | Authorized penetration testing only

---

## Features

### Module 1 — OSINT
- ✅ Carrier & country detection
- ✅ Number type (mobile/fixed/voip)
- ✅ Timezone lookup
- ✅ WhatsApp / Telegram presence check
- ✅ Data breach check
- ✅ Truecaller & Spokeo links

### Module 2 — Vulnerability Scan
- ⚡ SS7 protocol risk assessment
- 🔄 SIM Swap vulnerability check
- 📩 SMS OTP interception risk
- 📞 Caller ID spoofing risk
- 📬 Voicemail default PIN risk

---

## Install

```bash
git clone https://github.com/Youssefzdb/shadow-phone
cd shadow-phone
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Usage

```bash
# Interactive mode
python shadow_phone.py

# Direct mode
python shadow_phone.py +21612345678

# OSINT only
python shadow_phone.py +21612345678 --osint-only

# Vuln scan only
python shadow_phone.py +21612345678 --vuln-only
```

## Output

- Full colored terminal report
- Markdown report saved in `reports/`

---
*Shadow Red Team — Authorized use only*
