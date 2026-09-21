import streamlit as st
import base64
import math
from datetime import datetime
import io
from PIL import Image, ImageFile
from groq import Groq

ImageFile.LOAD_TRUNCATED_IMAGES = True

# Page Setup
st.set_page_config(page_title="ज्योतिष गुरु - WhatsApp Chat & Kundali", page_icon="🟢", layout="wide")

# --- Custom WhatsApp & Kundali CSS Styling ---
st.markdown("""
<style>
    .stApp { background-color: #efeae2; }
    .wa-header {
        background-color: #075e54; color: white; padding: 12px 18px;
        border-radius: 10px 10px 0 0; display: flex; align-items: center;
        gap: 12px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); margin-bottom: 15px;
    }
    .wa-avatar {
        width: 44px; height: 44px; border-radius: 50%; background-color: #dfdfdf;
        display: flex; align-items: center; justify-content: center; font-size: 22px;
    }
    .wa-header-info h4 { margin: 0; color: white; font-size: 17px; }
    .wa-header-info p { margin: 0; font-size: 12px; color: #d1f7e0; }
    .chat-container { display: flex; flex-direction: column; gap: 10px; padding: 10px; }
    .user-bubble {
        align-self: flex-end; background-color: #d9fdd3; color: #111b21;
        padding: 10px 14px; border-radius: 12px 0 12px 12px; max-width: 80%;
        font-size: 15px; box-shadow: 0 1px 2px rgba(0,0,0,0.15); word-wrap: break-word;
    }
    .guru-bubble {
        align-self: flex-start; background-color: #ffffff; color: #111b21;
        padding: 12px 16px; border-radius: 0 12px 12px 12px; max-width: 85%;
        font-size: 15px; box-shadow: 0 1px 2px rgba(0,0,0,0.15); word-wrap: break-word;
    }
    .sender-name { font-weight: bold; font-size: 11px; color: #075e54; margin-bottom: 3px; }
    .msg-time { font-size: 10px; color: #667781; text-align: right; margin-top: 4px; }
    .kundali-card {
        background-color: #ffffff; border-radius: 10px; padding: 15px;
        margin-bottom: 20px; box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        border-left: 5px solid #075e54;
    }
</style>
""", unsafe_allow_html=True)

NEPAL_PLACES = {
    "पोखरा (Pokhara, Kaski)": (28.2096, 83.9856),
    "काठमाडौँ (Kathmandu)": (27.7172, 85.3240),
    "ललितपुर (Lalitpur)": (27.6644, 85.3188),
    "भक्तपुर (Bhaktapur)": (27.6710, 85.4298),
    "विराटनगर (Biratnagar, Morang)": (26.4525, 87.2718),
    "वीरगञ्ज (Birgunj, Parsa)": (27.0128, 84.8774),
    "भरतपुर / चितवन (Bharatpur, Chitwan)": (27.6833, 84.4333),
    "बुटवल (Butwal, Rupandehi)": (27.7006, 83.4484),
    "धरान (Dharan, Sunsari)": (26.8124, 87.2834),
    "झापा / भद्रपुर (Bhadrapur, Jhapa)": (26.5417, 88.0894),
    "नेपालगञ्ज (Nepalgunj, Banke)": (28.0500, 81.6167),
    "धनगढी (Dhangadhi, Kailali)": (28.6852, 80.6080),
    "हेटौँडा (Hetauda, Makwanpur)": (27.4289, 85.0322),
    "जनकपुर (Janakpur, Dhanusha)": (26.7288, 85.9244),
    "अन्य / आफ्नै ठाउँ लेख्नुहोस्": (28.2096, 83.9856)
}

RASHIS = ["मेष (Mesh)", "वृषभ (Vrishabha)", "मिथुन (Mithun)", "कर्कट (Karka)",
          "सिंह (Simha)", "कन्या (Kanya)", "तुला (Tula)", "वृश्चिक (Vrishchik)",
          "धनु (Dhanu)", "मकर (Makar)", "कुम्भ (Kumbha)", "मीन (Meen)"]

NAKSHATRAS = [
    "अश्विनी", "भरणी", "कृत्तिका", "रोहिणी", "मृगशिरा", "आर्द्रा", "पुनर्वसु", "पुष्य", "अश्लेषा",
    "मघा", "पूर्वाफाल्गुनी", "उत्तराफाल्गुनी", "हस्त", "चित्रा", "स्वाती", "विशाखा", "अनुराधा", "ज्येष्ठा",
    "मूल", "पूर्वाषाढा", "उत्तराषाढा", "श्रवण", "धनिष्ठा", "शतभिषा", "पूर्वाभाद्रपद", "उत्तराभाद्रपद", "रेवती"
]

# --- सटिक वि.सं. देखि ई.सं. रूपान्तरण (Accurate BS to AD Calendar Table) ---
def bs_to_ad_accurate(bs_year, bs_month, bs_day):
    # बैशाख १ गतेको AD मिति तालिका (Base anchors)
    baisakh_1_map = {
        2055: (1998, 4, 14), 2056: (1999, 4, 14), 2057: (2000, 4, 13), 2058: (2001, 4, 13),
        2059: (2002, 4, 14), 2060: (2003, 4, 14), 2061: (2004, 4, 13), 2062: (2005, 4, 14),
        2063: (2006, 4, 14), 2064: (2007, 4, 14), 2065: (2008, 4, 13), 2066: (2009, 4, 14),
        2067: (2010, 4, 14), 2068: (2011, 4, 14), 2069: (2012, 4, 13), 2070: (2013, 4, 14),
        2071: (2014, 4, 14), 2072: (2015, 4, 14), 2073: (2016, 4, 13), 2074: (2017, 4, 14),
        2075: (2018, 4, 14), 2076: (2019, 4, 14), 2077: (2020, 4, 13), 2078: (2021, 4, 14),
        2079: (2022, 4, 14), 2080: (2023, 4, 14), 2081: (2024, 4, 13), 2082: (2025, 4, 14)
    }
    
    # यदि तालिकामा छ भने ठ्याक्कै निकाल्ने
    if bs_year in baisakh_1_map:
        ad_y, ad_m, ad_d = baisakh_1_map[bs_year]
        # महिनाको दिन जोड्ने
        month_offsets = [0, 31, 62, 93, 124, 155, 185, 215, 245, 274, 304, 334]
        total_days = month_offsets[bs_month - 1] + (bs_day - 1)
        
        # Datetime calculation
        from datetime import date, timedelta
        base_date = date(ad_y, ad_m, ad_d)
        target_date = base_date + timedelta(days=total_days)
        return target_date.year, target_date.month, target_date.day
    else:
        # Fallback
        ad_year = bs_year - 56 if bs_month >= 9 else bs_year - 57
        ad_month = (bs_month + 3) % 12 + 1
        return ad_year, ad_month, bs_day

# Astronomical Julian Day
def get_julian_day(year, month, day, hour=0):
    if month <= 2:
        year -= 1
        month += 12
    A = math.floor(year / 100)
    B = 2 - A + math.floor(A / 4)
    jd = math.floor(365.25 * (year + 4716)) + math.floor(30.6001 * (month + 1)) + day + B - 1524.5
    jd += hour / 24.0
    return jd

def calculate_accurate_vedic_chart(ad_year, ad_month, ad_day, tob_hour, tob_min, lon=83.9856):
    total_hour = tob_hour + (tob_min / 60.0) - 5.75 # Nepal NST (+5:45)
    jd = get_julian_day(ad_year, ad_month, ad_day, total_hour)
    
    # Lahiri Ayanamsha for 2000
    T = (jd - 2451545.0) / 36525.0
    ayanamsha = 23.85 + (1.396 * T)
    d = jd - 2451545.0

    def to_vedic(deg):
        v_deg = (deg - ayanamsha) % 360
        rashi_idx = int(v_deg // 30)
        degree_in_rashi = v_deg % 30
        return RASHIS[rashi_idx], degree_in_rashi, rashi_idx + 1

    # Accurate Sidereal Ephemeris Formulae
    sun_long = (280.460 + 0.9856474 * d) % 360
    
    # Moon: Mean anomaly + equation of center
    L = 218.316 + 13.176396 * d
    M = (134.963 + 13.064993 * d) * math.pi / 180.0
    moon_long = (L + 6.289 * math.sin(M)) % 360

    mars_long = (355.433 + 0.524033 * d) % 360
    jup_long = (34.351 + 0.083091 * d) % 360
    sat_long = (50.077 + 0.033459 * d) % 360
    rahu_long = (246.5 - 0.05295 * d) % 360
    ketu_long = (rahu_long + 180) % 360

    gst = (280.46061837 + 360.98564736629 * (jd - 2451545.0)) % 360
    lst = (gst + lon) % 360

    chart = {
        "लग्न (Lagna)": to_vedic(lst),
        "सूर्य (Sun)": to_vedic(sun_long),
        "चन्द्र (Moon)": to_vedic(moon_long),
        "मंगल (Mars)": to_vedic(mars_long),
        "बृहस्पति (Guru)": to_vedic(jup_long),
        "शनि (Saturn)": to_vedic(sat_long),
        "राहु (Rahu)": to_vedic(rahu_long),
        "केतु (Ketu)": to_vedic(ketu_long)
    }

    moon_vedic_deg = (moon_long - ayanamsha) % 360
    nakshatra_idx = int(moon_vedic_deg // 13.333333) % 27
    nakshatra_name = NAKSHATRAS[nakshatra_idx]

    dasha_lords = ["केतु", "शुक्र", "सूर्य", "चन्द्र", "मंगल", "राहु", "गुरु", "शनि", "बुध"]
    current_birth_lord = dasha_lords[nakshatra_idx % 9]

    moon_rashi = chart["चन्द्र (Moon)"][0]
    lagna_rashi = chart["लग्न (Lagna)"][0]

    return chart, lagna_rashi, moon_rashi, nakshatra_name, current_birth_lord

def render_north_indian_chart(chart, user_lagna_idx):
    lagna_num = user_lagna_idx
    houses = {i: [] for i in range(1, 13)}
    
    planet_abbrev = {
        "सूर्य (Sun)": "सू", "चन्द्र (Moon)": "चं", "मंगल (Mars)": "मं",
        "बृहस्पति (Guru)": "गु", "शनि (Saturn)": "श", "राहु (Rahu)": "रा", "केतु (Ketu)": "के"
    }

    for p_name, (r_name, deg, r_num) in chart.items():
        if p_name != "लग्न (Lagna)":
            house_no = ((r_num - lagna_num) % 12) + 1
            houses[house_no].append(planet_abbrev.get(p_name, p_name[:2]))

    def p_str(h_no):
        return " ".join(houses[h_no])

    svg = f"""
    <svg width="100%" height="320" viewBox="0 0 400 400" style="background:#fffaf0; border:2px solid #8b4513; border-radius:8px;">
        <rect x="10" y="10" width="380" height="380" fill="none" stroke="#8b4513" stroke-width="2"/>
        <line x1="10" y1="10" x2="390" y2="390" stroke="#8b4513" stroke-width="1.5"/>
        <line x1="10" y1="390" x2="390" y2="10" stroke="#8b4513" stroke-width="1.5"/>
        <polygon points="200,10 390,200 200,390 10,200" fill="none" stroke="#8b4513" stroke-width="2"/>
        
        <!-- House 1 (Lagna) -->
        <text x="200" y="70" font-size="13" fill="#b22222" text-anchor="middle" font-weight="bold">{lagna_num}</text>
        <text x="200" y="110" font-size="15" fill="#075e54" text-anchor="middle" font-weight="bold">{p_str(1)}</text>
        <text x="200" y="130" font-size="11" fill="#666" text-anchor="middle">१ (लग्न)</text>
        
        <!-- House 2 & 12 -->
        <text x="100" y="40" font-size="11" fill="#b22222" text-anchor="middle">{(lagna_num % 12) + 1}</text>
        <text x="110" y="80" font-size="13" fill="#075e54" text-anchor="middle">{p_str(2)}</text>
        <text x="300" y="40" font-size="11" fill="#b22222" text-anchor="middle">{((lagna_num + 10) % 12) + 1}</text>
        <text x="290" y="80" font-size="13" fill="#075e54" text-anchor="middle">{p_str(12)}</text>
        
        <!-- House 4 -->
        <text x="90" y="200" font-size="12" fill="#b22222" text-anchor="middle">{((lagna_num + 2) % 12) + 1}</text>
        <text x="90" y="220" font-size="13" fill="#075e54" text-anchor="middle">{p_str(4)}</text>
        
        <!-- House 7 -->
        <text x="200" y="340" font-size="12" fill="#b22222" text-anchor="middle">{((lagna_num + 5) % 12) + 1}</text>
        <text x="200" y="300" font-size="14" fill="#075e54" text-anchor="middle" font-weight="bold">{p_str(7)}</text>
        
        <!-- House 10 -->
        <text x="310" y="200" font-size="12" fill="#b22222" text-anchor="middle">{((lagna_num + 8) % 12) + 1}</text>
        <text x="310" y="220" font-size="13" fill="#075e54" text-anchor="middle">{p_str(10)}</text>
    </svg>
    """
    return svg

def optimize_and_encode_image(uploaded_file):
    if uploaded_file is None: return None
    try:
        uploaded_file.seek(0)
        img = Image.open(io.BytesIO(uploaded_file.read()))
        img.load()
        if img.mode != "RGB": img = img.convert("RGB")
        img.thumbnail((1024, 1024), Image.Resampling.LANCZOS)
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=85)
        return base64.b64encode(buf.getvalue()).decode('utf-8')
    except Exception:
        uploaded_file.seek(0)
        return base64.b64encode(uploaded_file.read()).decode('utf-8')

GROQ_VISION_MODEL = "qwen/qwen3.8-27b"

SYSTEM_PROMPT = """
तपाईं नेपालको परम्परागत सिद्धान्त ज्योतिष र सामुद्रिक हस्तरेखा शास्त्रका परम विद्वान 'ज्योतिषाचार्य' हुनुहुन्छ।
प्रयोगकर्ताको वास्तविक कुण्डली र हातको रेखाको आधारमा विक्रम संवत् (वि.सं.) को वर्ष/महिना तोकेर ठोस शास्त्रीय कारणसहित शुद्ध नेपालीमा फलादेश दिनुहोस्।
"""

# --- Sidebar Inputs ---
with st.sidebar:
    st.markdown("### 📋 जन्म विवरण (वि.सं.)")
    
    nepali_months = ["१. बैशाख", "२. जेठ", "३. असार", "४. साउन", "५. भदौ", "६. असोज", 
                     "७. कात्तिक", "८. मङ्सिर", "९. पुस", "१०. माघ", "११. फागुन", "१२. चैत"]
    
    col_y, col_m, col_d = st.columns(3)
    with col_y:
        bs_year = st.selectbox("वर्ष (वि.सं.)", list(range(2083, 2030, -1)), index=31) # 2057 default
    with col_m:
        bs_month_str = st.selectbox("महिना", nepali_months, index=0)
        bs_month = int(bs_month_str.split(".")[0])
    with col_d:
        bs_day = st.selectbox("गते", list(range(1, 33)), index=11) # 12 default

    tob = st.time_input("जन्म समय (Birth Time):", value=datetime.strptime("13:15:00", "%H:%M:%S").time())

    selected_place = st.selectbox("जन्म स्थान:", list(NEPAL_PLACES.keys()), index=0)
    place_lon = NEPAL_PLACES[selected_place][1]
    place_name = selected_place

    gender = st.selectbox("लिङ्ग:", ["पुरुष", "महिला", "अन्य"])

    # Compute Initial Astrological Chart
    ad_y, ad_m, ad_d = bs_to_ad_accurate(bs_year, bs_month, bs_day)
    chart_data, calc_lagna, calc_moon, calc_nak, birth_dasha = calculate_accurate_vedic_chart(
        ad_y, ad_m, ad_d, tob.hour, tob.minute, lon=place_lon
    )

    st.markdown("---")
    st.markdown("### 🛠️ कुण्डली सच्याउने सुविधा (Manual Override)")
    st.info("यदि हजुरको पात्रो/कुण्डलीमा लग्न वा राशि फरक छ भने यहाँबाट सिधै रोज्नुहोस्:")
    
    # प्रयोगकर्ताले सिधै आफ्नो सही लग्न र राशि छान्ने सुविधा
    user_lagna = st.selectbox("हजुरको वास्तविक लग्न:", RASHIS, index=RASHIS.index(calc_lagna) if calc_lagna in RASHIS else 3)
    user_rashi = st.selectbox("हजुरको वास्तविक चन्द्र राशि:", RASHIS, index=RASHIS.index(calc_moon) if calc_moon in RASHIS else 8)
    user_nakshatra = st.selectbox("हजुरको नक्षत्र:", NAKSHATRAS, index=NAKSHATRAS.index(calc_nak) if calc_nak in NAKSHATRAS else 18)

    st.markdown("---")
    st.markdown("### 📸 फोटोहरू अपलोड")
    chart_files = st.file_uploader("१. कुण्डलीका फोटोहरू (जति पनि)", type=["jpg", "jpeg", "png"], accept_multiple_files=True)
    palm_files = st.file_uploader("२. हातका फोटोहरू (दाहिने/देब्रे दुवै)", type=["jpg", "jpeg", "png"], accept_multiple_files=True)

    default_key = st.secrets.get("GROQ_API_KEY", "")
    if not default_key:
        groq_api_key = st.text_input("Groq Key:", type="password")
    else:
        groq_api_key = default_key

    start_chat = st.button("🟢 कुण्डली जाँच्नुहोस् र कुराकानी सुरु गर्नुहोस्", use_container_width=True)

# --- Header ---
st.markdown("""
<div class="wa-header">
    <div class="wa-avatar">🧘‍♂️</div>
    <div class="wa-header-info">
        <h4>पूज्य ज्योतिषाचार्य (गुरुजी)</h4>
        <p>🟢 अनलाइन | शुद्ध वि.सं. पञ्चाङ्ग र कुण्डली चक्र</p>
    </div>
</div>
""", unsafe_allow_html=True)

user_lagna_idx = RASHIS.index(user_lagna) + 1

# --- Display Verified Kundali Card ---
st.markdown('<div class="kundali-card">', unsafe_allow_html=True)
st.subheader("🪐 प्रमाणित जन्म कुण्डली तथा पञ्चाङ्ग विवरण")
col_k1, col_k2 = st.columns([1.1, 1])

with col_k1:
    st.markdown(render_north_indian_chart(chart_data, user_lagna_idx), unsafe_allow_html=True)

with col_k2:
    st.markdown(f"""
    * **जन्म मिति:** वि.सं. `{bs_year}/{bs_month}/{bs_day}` (ई.सं. `{ad_y}-{ad_m:02d}-{ad_d:02d}`)
    * **जन्म समय:** `{tob}` | **स्थान:** `{place_name}`
    * **लग्न (Ascendant):** **{user_lagna}**
    * **जन्म राशि (Moon Sign):** **{user_rashi}**
    * **जन्म नक्षत्र:** **{user_nakshatra}**
    * **जन्म महादशा स्वामी:** **{birth_dasha}**
    """)
    st.markdown("---")
    st.markdown("**ग्रहहरूको स्पष्ट डिग्री र राशि:**")
    for p_name, (r_name, deg, _) in list(chart_data.items())[1:]:
        st.write(f"• **{p_name}:** {r_name} — `{deg:.2f}°`")
st.markdown('</div>', unsafe_allow_html=True)

# Session State for Messages
if "messages" not in st.session_state:
    st.session_state.messages = []

# When Start Chat is clicked
if start_chat:
    if not groq_api_key:
        st.error("कृपया Groq API Key हाल्नुहोस्!")
    else:
        verified_summary = f"""--- आधिकारिक जन्म कुण्डली विवरण ---
जन्म मिति: वि.सं. {bs_year}/{bs_month}/{bs_day} (AD: {ad_y}-{ad_m:02d}-{ad_d:02d})
जन्म समय: {tob}, स्थान: {place_name}
प्रमाणित लग्न: {user_lagna}
प्रमाणित चन्द्र राशि: {user_rashi}
जन्म नक्षत्र: {user_nakshatra}
जन्म महादशा: {birth_dasha}
"""
        for planet, (rashi, deg, _) in chart_data.items():
            verified_summary += f"{planet}: {rashi} ({deg:.2f}°)\n"

        user_content = [
            {
                "type": "text", 
                "text": f"""प्रणाम गुरुज्यू! 
मेरो प्रमाणित कुण्डली विवरण यस प्रकार छ:
{verified_summary}

कृपया:
१. मेरो प्रमाणित लग्न ({user_lagna}), चन्द्र राशि ({user_rashi}), नक्षत्र ({user_nakshatra}), र संलग्न हातका फोटोहरूको आधारमा अध्ययन गर्नुहोस्।
२. सिधै विक्रम संवत् (वि.सं.) को वर्ष र महिना तोकेर कारणसहित मेरो प्रारम्भिक फलादेश शुद्ध नेपालीमा दिनुहोस्।"""
            }
        ]

        if chart_files:
            for c_file in chart_files:
                b64 = optimize_and_encode_image(c_file)
                if b64: user_content.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}})

        if palm_files:
            for p_file in palm_files:
                b64 = optimize_and_encode_image(p_file)
                if b64: user_content.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}})

        client = Groq(api_key=groq_api_key)
        with st.spinner("गुरुजीले प्रमाणित कुण्डली र हस्तरेखा अध्ययन गर्दै हुनुहुन्छ..."):
            try:
                response = client.chat.completions.create(
                    model=GROQ_VISION_MODEL,
                    messages=[{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": user_content}],
                    temperature=0.6,
                    max_tokens=2048
                )
                guru_reply = response.choices[0].message.content
                st.session_state.messages = [
                    {"role": "user", "content": f"प्रणाम गुरुज्यू, मेरो कुण्डली (लग्न: {user_lagna}, राशि: {user_rashi}) र हात हेरिदिनुहोस्।", "time": datetime.now().strftime("%I:%M %p")},
                    {"role": "assistant", "content": guru_reply, "time": datetime.now().strftime("%I:%M %p")}
                ]
            except Exception as e:
                # Backup model
                try:
                    response = client.chat.completions.create(
                        model="meta-llama/llama-4-scout-17b-16e-instruct",
                        messages=[{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": user_content}],
                        temperature=0.6,
                        max_tokens=2048
                    )
                    guru_reply = response.choices[0].message.content
                    st.session_state.messages = [
                        {"role": "user", "content": f"प्रणाम गुरुज्यू, मेरो कुण्डली र हात हेरिदिनुहोस्।", "time": datetime.now().strftime("%I:%M %p")},
                        {"role": "assistant", "content": guru_reply, "time": datetime.now().strftime("%I:%M %p")}
                    ]
                except Exception as e2:
                    st.error(f"त्रुटि: {str(e2)}")

# --- Render WhatsApp Chat Messages ---
st.markdown('<div class="chat-container">', unsafe_allow_html=True)
for msg in st.session_state.messages:
    t = msg.get("time", "")
    if msg["role"] == "user":
        st.markdown(f'<div class="user-bubble"><div>{msg["content"]}</div><div class="msg-time">{t} ✓✓</div></div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="guru-bubble"><div class="sender-name">पूज्य ज्योतिषाचार्य</div><div>{msg["content"]}</div><div class="msg-time">{t}</div></div>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

# --- Interactive Chat Input ---
if user_question := st.chat_input("यहाँ सन्देश लेख्नुहोस् (कुनै पनि विषय: करियर, विवाह, विदेश, स्वास्थ्य...)..."):
    if not groq_api_key:
        st.warning("कृपया पहिले Groq API Key हाल्नुहोस्!")
    else:
        current_time = datetime.now().strftime("%I:%M %p")
        st.session_state.messages.append({"role": "user", "content": user_question, "time": current_time})

        client = Groq(api_key=groq_api_key)
        with st.spinner("गुरुजी विश्लेषण गर्दै हुनुहुन्छ..."):
            try:
                api_messages = [{"role": "system", "content": SYSTEM_PROMPT}]
                for m in st.session_state.messages:
                    api_messages.append({"role": m["role"], "content": m["content"]})

                response = client.chat.completions.create(
                    model=GROQ_VISION_MODEL,
                    messages=api_messages,
                    temperature=0.6,
                    max_tokens=1500
                )
                reply = response.choices[0].message.content
                st.session_state.messages.append({"role": "assistant", "content": reply, "time": datetime.now().strftime("%I:%M %p")})
                st.rerun()
            except Exception as e:
                try:
                    response = client.chat.completions.create(
                        model="meta-llama/llama-4-scout-17b-16e-instruct",
                        messages=api_messages,
                        temperature=0.6,
                        max_tokens=1500
                    )
                    reply = response.choices[0].message.content
                    st.session_state.messages.append({"role": "assistant", "content": reply, "time": datetime.now().strftime("%I:%M %p")})
                    st.rerun()
                except Exception as e2:
                    st.error(f"त्रुटि: {str(e2)}")
