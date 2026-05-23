# Week 1: Problem Validation – AfriTrade Agent

**Crew:** Team‑Africod  
**Members:** Zerihun Asrat (Ethiopia), Aja Corneli (Nigeria), and Patience Nzomuhoza (Burundi)   
**Date:** 23 May 2026  

---

## 1. The Problem (One Sentence)

> Informal cross‑border traders in Africa lose 3–7 hours per trip navigating unpredictable tariffs, route closures, and real‑time currency rates because no free, voice‑first, pan‑African assistant exists.

---

## 2. Target User Persona (Regionalised by creew members)

| Country | Persona | Goods | Key Pain Point |
|---------|---------|-------|----------------|
| **Ethiopia** | Habtamu Tsegaye (40, Addis–Nairobi route (Moyale)) | Electronics, Clothes | Unclear transit fees at Moyale border; tite regulation, no real‑time forex for Kenyan shilling |
| **Nigeria** | Fatima (40, Lagos–Accra/Cotonou) | Phone parts, textiles | Relies on middlemen who charge 10–15% for tariff advice; cannot read long customs PDFs |
| **Burundi** | Jean (32, Bujumbura–Goma/Kigali) | Beans, palm oil | Frequent route closures; low literacy in French/English; needs Kirundi voice support |

All three use feature phones (voice and text are primary interfaces).

---

## 3. Data Collection Methods

| Method | What we did | Evidence collected |
|--------|-------------|--------------------|
| **Public datasets** | Downloaded ECOWAS Common External Tariff (CET) 2025 PDFs, EAC Common Tariff (2024), COMESA guidelines, World Bank border wait times. | 22 PDFs, 4 CSV files (border corridors) |
| **Direct interviews (remote & difficult to get the information)** | Each crew member interviewed 1 to 3 informal traders in their respective country (WhatsApp voice, telegram recorded with permission). Total 6 traders. | 4 audio recordings + written notes (anonymised) |
| **Community validation** | Posted in 3 regional trade WhatsApp groups (Ethiopia–Kenya, Nigeria–Benin, Burundi–DRC). | 32 responses – top answer: “knowing the real tariff before I leave” (68%) |

### Key quantitative findings (mean of value)

- Average reported time wasted per border crossing: **4.7 hours**
- Average unofficial payment for “tariff clarification”: **~$7 USD** (significant for informal traders)
- 71% of traders said they would use a **free voice assistant daily** if it worked in their local language (Amharic, Pidgin, Kirundi mix)

---

## 4. Interview Summary (Anonymised)

| Trader | Route | Product | Most frequent question | Current solution |
|--------|-------|---------|------------------------|------------------|
| T‑ET01 | Addis–Nairobi | Coffee | “What tax at Moyale?” | Ask friends who crossed last week |
| T‑ET02 | Addis–Djibouti | Khat | “Is the port open?” | Radio / word of mouth |
| T‑ET03 | Mekelle–Adigrat | Barley | “Exchange rate today?” | Black market – often outdated |
| T‑NG01 | Abuja–Accra | Phones | “Tariff for 50 smartphones?” | Pays a broker 10% of goods value |
| T‑NG02 | Kano–Maradi (Niger) | Leather | “Road closure near border?” | Waits and asks other drivers |
| T‑NG03 | Lagos–Cotonou | Rice | “Is the 5% levy still active?” | Guesses – sometimes overpays 20% |
| T‑BI01 | Bujumbura–Goma | Beans | “Which route is safe today?” | Relies on motorcycle taxis who charge double |
| T‑BI02 | Bujumbura–Kigali | Palm oil | “What documents needed?” | Pays a “facilitator” $5 per trip |
| T‑BI03 | Gitega–Kibuye | Vegetables | “Franc congolais rate?” | Asks at multiple stalls, loses 2 hours |

---

## 5. Problem–Solution Fit Statement

> *A voice agent that answers tariff, route, and currency queries in under 10 seconds using only free public data would save each trader ~100 hours per year and reduce corruption at borders. No existing tool provides this for free, in local languages (Amharic, Pidgin, Kirundi), across East and West African corridors.*

---

## 6. How We Will Solve It (Blueprint Summary)

| Component | Free Technology | Week |
|-----------|----------------|------|
| Speech‑to‑text | Whisper (Hugging Face-free tier) | on Week 4 |
| Intent routing | Gemini model 3.1 flash/Gemini Omni (free tier) | will be performed on Week 3 |
| Tariff retrieval | Qdrant vector DB (1GB free) + embeddings | this will be on Week 2 |
| Route graph | Neo4j AuraDB free (Cypher queries) | will be solve by Week 2 |
| Currency | Frankfurter API (free) | Week 3 |
| Tester‑input API | FastAPI on Render free | Week 3 |
| Voice output | Web Speech API (client‑side, no cost) | Week 4 |

---

## 7. Validation of the Need (Real Quotes)

> *“I have to waste half my day at Seme border just to get and ask a right person about what the real tax is. If my phone could tell me, I would use that time and cross twice the border.”* – Fatima, Lagos

> *“It's fact the harsh trade condition exist nowadays at Moyale, the rate changes every day, if not hour. I lose at least 500 birr each time because nobody tells me the trend.”* – Habtamu Tsegaye, Addis Ababa

> *“I don't read French. The customs paper means nothing to me. Just speak to me in Kirundi.”* – Jean, Bujumbura

---

## Appendix: Links to Raw Data

- [ECOWAS CET 2025 (PDF)](https://example.com/ecowas-cet.pdf) – downloaded and stored in `/data`
- [EAC Common Tariff (PDF)](https://example.com/eac-tariff.pdf)
- [World Bank Border Wait Times (CSV)](https://example.com/border-wait.csv)
- Interview notes (anonymised): `/week1/interviews/`

*All data obtained legally and used only for non‑commercial, educational purposes within The Build.*
