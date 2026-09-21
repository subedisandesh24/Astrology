import streamlit as st
import base64
import math
from datetime import datetime
import io
from PIL import Image, ImageFile
from groq import Groq

# Truncated वा मोबाइलका तस्बिरहरू नबिग्रिउन् भनी सुरक्षित गर्ने
ImageFile.LOAD_TRUNCATED_IMAGES = True

# Page Setup
st.set_page_config(page_title="ज्योतिष गुरु - WhatsApp Chat & Kundali", page_icon="🟢", layout="wide")

# --- Custom WhatsApp & Kundali CSS Styling ---
st.markdown("""
<style>
    .stApp { background-color: #efeae2; }
    .wa-header {
        background-color: #075e54;
        color: white;
        padding: 12px 18px;
        border-radius: 10px 10px 0 0;
        display: flex;
        align-items: center;
        gap: 12px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin-bottom: 15px;
    }
    .wa-avatar {
        width: 44px; height: 44px; border-radius: 50%;
        background-color: #dfdfdf; display: flex;
        align-items: center; justify-content: center; font-size: 22px;
    }
    .wa-header-info h4 { margin: 0; color: white; font-size: 17px; }
    .wa-header-info p { margin: 0; font-size: 12px; color: #d1f7e0; }
    .chat-container { display: flex; flex-direction: column; gap: 10px; padding: 10px; }
    .user-bubble {
        align-self: flex-end; background-color: #d9fdd3; color: #111b21;
        padding: 10px 14px; border-radius: 12px 0 12px 12px;
        max-width: 80%; font-size: 15px; box-shadow: 0 1px 2px rgba(0,0,0,0.15);
        word-wrap: break-word; line-height: 1.5;
    }
    .guru-bubble {
        align-self: flex-start; background-color: #ffffff; color: #111b21;
        padding: 12px 16px; border-radius: 0 12px 12px 12px;
        max-width: 85%; font-size: 15px; box-shadow: 0 1px 2px rgba(0,0,0,0.15);
        word-wrap: break-word; line-height: 1.6;
    }
    .sender-name { font-weight: bold; font-size: 11px; color: #075e54; margin-bottom: 3px; }
    .msg-time { font-size: 10px; color: #667781; text-align: right; margin-top: 4px; }
    
    /* कुण्डली कार्ड स्टाइल */
    .kundali-card {
        background-color: #ffffff;
        border-radius: 10px;
        padding: 15px;
        margin-bottom: 20px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        border-left: 5px solid #075e54;
    }
</style>
""", unsafe_allow_html=True)

# नेपालका प्रमुख सहर/जिल्लाहरू
NEPAL_PLACES = {
    "काठमाडौँ (Kathmandu)": (27.7172, 85.3240),
    "ललितपुर (Lalitpur)": (27.6644, 85.3188),
    "भक्तपुर (Bhaktapur)": (27.6710, 85.4298),
    "पोखरा (Pokhara, Kaski)": (28.2096, 83.9856),
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
    "इटहरी (Itahari, Sunsari)": (26.6667, 87.2833),
    "दाङ / घोराही (Ghorahi, Dang)": (28.0333, 82.5000),
    "सुर्खेत / वीरेन्द्रनगर (Birendranagar, Surkhet)": (28.6000, 81.6333),
    "बाग्लुङ (Baglung)": (28.2719, 83.5898),
    "पाल्पा / तानसेन (Tansen, Palpa)": (27.8667, 83.5500),
    "इलाम (Ilam)": (26.9089, 87.9265),
    "कञ्चनपुर / महेन्द्रनगर (Mahendranagar, Kanchanpur)": (28.9667, 80.1833),
    "अन्य / आफ्नै ठाउँ टाइप गर्नुहोस् (Custom Place)": (27.7172, 85.3240)
}

NAKSHATRAS = [
    "अश्विनी", "भरणी", "कृत्तिका", "रोहिणी", "मृगशिरा", "आर्द्रा", "पुनर्वसु", "पुष्य", "अश्लेषा",
    "मघा", "पूर्वाफाल्गुनी", "उत्तराफाल्गुनी", "हस्त", "चित्रा", "स्वाती", "विशाखा", "अनुराधा", "ज्येष्ठा",
    "मूल", "पूर्वाषाढा", "उत्तराषाढा", "श्रवण", "धनिष्ठा", "शतभिषा", "पूर्वाभाद्रपद", "उत्तराभाद्रपद", "रेवती"
]

# BS to AD Conversion
def bs_to_ad_approx(bs_year, bs_month, bs_day):
    ad_year = bs_year - 56 if bs_month >= 9 else bs_year - 57
    ad_month = (bs_month + 8) % 12
    if ad_month == 0: ad_month = 12
    ad_day = (bs_day + 13) % 30
    if ad_day == 0: ad_day = 1
    return ad_year, ad_month, ad_day

# Mathematical Degree Calculation
def get_julian_day(year, month, day, hour=0):
    if month <= 2:
        year -= 1
        month += 12
    A = math.floor(year / 100)
    B = 2 - A + math.floor(A / 4)
    jd = math.floor(365.25 * (year + 4716)) + math.floor(30.6001 * (month + 1)) + day + B - 1524.5
    jd += hour / 24.0
    return jd

def calculate_approx_vedic_chart(ad_year, ad_month, ad_day, tob_hour, tob_min, lon=85.3240):
    total_hour = tob_hour + (tob_min / 60.0) - 5.75
    jd = get_julian_day(ad_year, ad_month, ad_day, total_hour)
    T = (jd - 2451545.0) / 36525.0
    ayanamsha = 23.85 + (1.396 * T)
    d = jd - 2451545.0

    rashis = ["मेष (Mesh)", "वृषभ (Vrishabha)", "मिथुन (Mithun)", "कर्कट (Karka)",
              "सिंह (Simha)", "कन्या (Kanya)", "तुला (Tula)", "वृश्चिक (Vrishchik)",
              "धनु (Dhanu)", "मकर (Makar)", "कुम्भ (Kumbha)", "मीन (Meen)"]
    
    def to_vedic(deg):
        v_deg = (deg - ayanamsha) % 360
        rashi_idx = int(v_deg // 30)
        degree_in_rashi = v_deg % 30
        return rashis[rashi_idx], degree_in_rashi, rashi_idx + 1

    sun_long = (280.460 + 0.9856474 * d) % 360
    moon_long = (218.316 + 13.176396 * d) % 360
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

    # नक्षत्र र महादशा
    moon_vedic_deg = (moon_long - ayanamsha) % 360
    nakshatra_idx = int(moon_vedic_deg // 13.333333) % 27
    nakshatra_name = NAKSHATRAS[nakshatra_idx]

    dasha_lords = ["केतु", "शुक्र", "सूर्य", "चन्द्र", "मंगल", "राहु", "गुरु", "शनि", "बुध"]
    current_birth_lord = dasha_lords[nakshatra_idx % 9]

    # चन्द्र राशि (Birth Sign)
    moon_rashi = chart["चन्द्र (Moon)"][0]
    lagna_rashi = chart["लग्न (Lagna)"][0]

    return chart, lagna_rashi, moon_rashi, nakshatra_name, current_birth_lord

# --- पारम्परिक नेपाली कुण्डली चक्र बनाउने (North Indian SVG Chart) ---
def render_north_indian_chart(chart):
    lagna_num = chart["लग्न (Lagna)"][2]
    
    # १२ वटा भावमा बस्ने ग्रहहरूको सूची बनाउने
    houses = {i: [] for i in range(1, 13)}
    
    planet_abbrev = {
        "सूर्य (Sun)": "सू",
        "चन्द्र (Moon)": "चं",
        "मंगल (Mars)": "मं",
        "बृहस्पति (Guru)": "गु",
        "शनि (Saturn)": "श",
        "राहु (Rahu)": "रा",
        "केतु (Ketu)": "के"
    }

    for p_name, (r_name, deg, r_num) in chart.items():
        if p_name != "लग्न (Lagna)":
            # भाव पत्ता लगाउने
            house_no = ((r_num - lagna_num) % 12) + 1
            houses[house_no].append(planet_abbrev.get(p_name, p_name[:2]))

    def p_str(h_no):
        return " ".join(houses[h_no])

    # SVG Diagram
    svg = f"""
    <svg width="100%" height="320" viewBox="0 0 400 400" style="background:#fffaf0; border:2px solid #8b4513; border-radius:8px;">
        <!-- Outer boundary -->
        <rect x="10" y="10" width="380" height="380" fill="none" stroke="#8b4513" stroke-width="2"/>
        <!-- Diagonals -->
        <line x1="10" y1="10" x2="390" y2="390" stroke="#8b4513" stroke-width="1.5"/>
        <line x1="10" y1="390" x2="390" y2="10" stroke="#8b4513" stroke-width="1.5"/>
        <!-- Inner Diamond -->
        <polygon points="200,10 390,200 200,390 10,200" fill="none" stroke="#8b4513" stroke-width="2"/>
        
        <!-- House 1 (Top Center Diamond) -->
        <text x="200" y="70" font-size="12" fill="#b22222" text-anchor="middle" font-weight="bold">{lagna_num}</text>
        <text x="200" y="110" font-size="14" fill="#075e54" text-anchor="middle" font-weight="bold">{p_str(1)}</text>
        <text x="200" y="130" font-size="11" fill="#666" text-anchor="middle">१ (तनु/लग्न)</text>
        
        <!-- House 2 -->
        <text x="100" y="40" font-size="11" fill="#b22222" text-anchor="middle">{(lagna_num % 12) + 1}</text>
        <text x="110" y="80" font-size="13" fill="#075e54" text-anchor="middle">{p_str(2)}</text>
        
        <!-- House 12 -->
        <text x="300" y="40" font-size="11" fill="#b22222" text-anchor="middle">{((lagna_num + 10) % 12) + 1}</text>
        <text x="290" y="80" font-size="13" fill="#075e54" text-anchor="middle">{p_str(12)}</text>
        
        <!-- House 4 -->
        <text x="90" y="200" font-size="12" fill="#b22222" text-anchor="middle">{((lagna_num + 2) % 12) + 1}</text>
        <text x="90" y="220" font-size="13" fill="#075e54" text-anchor="middle">{p_str(4)}</text>
        
        <!-- House 7 (Bottom Center Diamond) -->
        <text x="200" y="340" font-size="12" fill="#b22222" text-anchor="middle">{((lagna_num + 5) % 12) + 1}</text>
        <text x="200" y="300" font-size="14" fill="#075e54" text-anchor="middle" font-weight="bold">{p_str(7)}</text>
        
        <!-- House 10 (Right Center Diamond) -->
        <text x="310" y="200" font-size="12" fill="#b22222" text-anchor="middle">{((lagna_num + 8) % 12) + 1}</text>
        <text x="310" y="220" font-size="13" fill="#075e54" text-anchor="middle">{p_str(10)}</text>
    </svg>
    """
    return svg

def optimize_and_encode_image(uploaded_file):
    if uploaded_file is None:
        return None
    try:
        uploaded_file.seek(0)
        file_bytes = uploaded_file.read()
        img = Image.open(io.BytesIO(file_bytes))
        img.load()
        if img.mode != "RGB":
            img = img.convert("RGB")
        img.thumbnail((1024, 1024), Image.Resampling.LANCZOS)
        buffer = io.BytesIO()
        img.save(buffer, format="JPEG", quality=85)
        return base64.b64encode(buffer.getvalue()).decode('utf-8')
    except Exception:
        uploaded_file.seek(0)
        return base64.b64encode(uploaded_file.read()).decode('utf-8')

# सक्रिय Groq Vision मोडेल
GROQ_VISION_MODEL = "qwen/qwen3.8-27b"

SYSTEM_PROMPT = """
तपाईं नेपालको परम्परागत सिद्धान्त ज्योतिष, फलित ज्योतिष, र सामुद्रिक हस्तरेखा शास्त्रका परम विद्वान 'ज्योतिषाचार्य' हुनुहुन्छ।

मुख्य कार्यसम्पादन नियमहरू:
१. कुण्डली तालिका र चक्रको मिलान (Verification):
   - सिस्टमले स्क्रीनमा देखाएको लग्न, राशि, नक्षत्र, र ग्रह डिग्रीहरूलाई प्रयोगकर्ताको अपलोड गरिएको कुण्डलीसँग मिलाउनुहोस्।
   - यदि केही भिन्नता भएमा प्रयोगकर्तालाई सन्तुष्ट हुने गरी स्पष्ट कारण खुलाउनुहोस्।

२. दुवै हातको विश्लेषण (Dual-Hand Palmistry):
   - देब्रे हात (जन्मजात भाग्य) र दाहिने हात (वर्तमान कर्म र पुरुषार्थ) दुवैलाई दाँजेर फलादेश दिनुहोस्।

३. समय र मिति (Strict BS Timeline):
   - अनिवार्य रूपमा नेपाली विक्रम संवत् (वि.सं.) को वर्ष र महिना तोकेर बोल्नुहोस् (उदा: "२०८३ असार मसान्तभित्र...").

४. ठोस शास्त्रीय कारण (Mandatory Reasoning):
   - फलादेश गर्दा महादशा, अन्तर्दशा, गोचर, ग्रहको दृष्टि, र हातको सम्बन्धित रेखा/पर्वतको अवस्था अनिवार्य खुलाउनुहोस्।

५. भाषा शैली:
   - सधैं शुद्ध, आदरार्थी, र स्पष्ट नेपाली भाषा (देवनागरी लिपि) मा संवाद गर्नुहोस्।
"""

# --- Sidebar: Direct Birth Details ---
with st.sidebar:
    st.markdown("### 📋 जन्म विवरण (वि.सं.)")
    
    nepali_months = ["१. बैशाख", "२. जेठ", "३. असार", "४. साउन", "५. भदौ", "६. असोज", 
                     "७. कात्तिक", "८. मङ्सिर", "९. पुस", "१०. माघ", "११. फागुन", "१२. चैत"]
    
    col_y, col_m, col_d = st.columns(3)
    with col_y:
        bs_year = st.selectbox("वर्ष (वि.सं.)", list(range(2083, 2030, -1)), index=30)
    with col_m:
        bs_month_str = st.selectbox("महिना", nepali_months, index=0)
        bs_month = int(bs_month_str.split(".")[0])
    with col_d:
        bs_day = st.selectbox("गते", list(range(1, 33)), index=0)

    tob = st.time_input("जन्म समय (Birth Time):")

    st.markdown("**जन्म स्थान (Place):**")
    selected_place = st.selectbox("नेपालका प्रमुख सहर/जिल्ला:", list(NEPAL_PLACES.keys()))
    
    if "अन्य" in selected_place:
        custom_place = st.text_input("आफ्नो ठाउँको नाम लेख्नुहोस् (नेपाली वा English मा):", value="Kathmandu")
        place_name = custom_place
        place_lon = 85.3240
    else:
        place_name = selected_place
        place_lon = NEPAL_PLACES[selected_place][1]
    
    gender = st.selectbox("लिङ्ग:", ["पुरुष", "महिला", "अन्य"])

    st.markdown("---")
    st.markdown("### 📸 फोटोहरू अपलोड")
    chart_files = st.file_uploader("१. कुण्डलीका फोटोहरू (जति पनि)", type=["jpg", "jpeg", "png"], accept_multiple_files=True)
    palm_files = st.file_uploader("२. हातका फोटोहरू (दाहिने र देब्रे दुवै)", type=["jpg", "jpeg", "png"], accept_multiple_files=True)

    past_event = st.text_input("विगतको मुख्य घटना (ऐच्छिक - समय जाँच्न):", placeholder="उदा: २०७८ मा जागिर सुरु")

    default_key = st.secrets.get("GROQ_API_KEY", "")
    if not default_key:
        groq_api_key = st.text_input("Groq Key:", type="password")
    else:
        groq_api_key = default_key

    generate_kundali = st.button("🔮 पहिले कुण्डली चक्र र विवरण हेर्नुहोस्", use_container_width=True)

# --- Header ---
st.markdown("""
<div class="wa-header">
    <div class="wa-avatar">🧘‍♂️</div>
    <div class="wa-header-info">
        <h4>पूज्य ज्योतिषाचार्य (गुरुजी)</h4>
        <p>🟢 अनलाइन | कुण्डली चक्र, ग्रह डिग्री र वि.सं. अनुसार फलादेश</p>
    </div>
</div>
""", unsafe_allow_html=True)

# Calculation
ad_y, ad_m, ad_d = bs_to_ad_approx(bs_year, bs_month, bs_day)
chart_data, lagna_rashi, moon_rashi, nakshatra_name, birth_dasha = calculate_approx_vedic_chart(
    ad_y, ad_m, ad_d, tob.hour, tob.minute, lon=place_lon
)

# --- कुण्डली चक्र र पञ्चाङ्ग विवरण स्क्रीनमै देखाउने ---
st.markdown('<div class="kundali-card">', unsafe_allow_html=True)
st.subheader("🪐 कम्प्युटर गणना: लग्न कुण्डली चक्र तथा ग्रह स्पष्ट डिग्री")
st.markdown("*तपाईंको कुण्डलीसँग मिलाएर हेर्नुहोस् (Lagna, Rashi, Degree & Nakshatra Verification):*")

col_k1, col_k2 = st.columns([1.1, 1])

with col_k1:
    # परम्परागत कुण्डली चक्र
    st.markdown(render_north_indian_chart(chart_data), unsafe_allow_html=True)

with col_k2:
    st.markdown(f"""
    * **जन्म मिति:** वि.सं. `{bs_year}/{bs_month}/{bs_day}` (समय: `{tob}`)
    * **स्थान:** `{place_name}`
    * **लग्न (Ascendant):** **{lagna_rashi}** (`{chart_data['लग्न (Lagna)'][1]:.2f}°`)
    * **जन्म राशि (Moon Sign):** **{moon_rashi}**
    * **जन्म नक्षत्र:** **{nakshatra_name}**
    * **जन्म महादशा स्वामी:** **{birth_dasha}**
    """)
    st.markdown("---")
    st.markdown("**ग्रहहरूको स्पष्ट डिग्री र राशि:**")
    for p_name, (r_name, deg, _) in list(chart_data.items())[1:]:
        st.write(f"• **{p_name}:** {r_name} — `{deg:.2f}°`")

st.markdown('</div>', unsafe_allow_html=True)

# Session Messages
if "messages" not in st.session_state:
    st.session_state.messages = []

# बटन थिचेपछि मात्र च्याट सुरु हुने
if generate_kundali:
    if not groq_api_key:
        st.error("कृपया पहिले Groq API Key हाल्नुहोस्!")
    else:
        degree_summary = f"--- कम्प्युटर गणना कुण्डली ---\nजन्म मिति: वि.सं. {bs_year}/{bs_month}/{bs_day}, समय: {tob}, स्थान: {place_name}\n"
        degree_summary += f"लग्न: {lagna_rashi}, चन्द्र राशि: {moon_rashi}, नक्षत्र: {nakshatra_name}\n"
        degree_summary += f"जन्म महादशा: {birth_dasha}\n"
        for planet, (rashi, deg, _) in chart_data.items():
            degree_summary += f"{planet}: {rashi} ({deg:.2f}°)\n"

        user_content = [
            {
                "type": "text", 
                "text": f"""प्रणाम गुरुज्यू! 
सिस्टमले निकालेको मेरो कुण्डली विवरण यस प्रकार छ:
{degree_summary}

कृपया:
१. सिस्टमले स्क्रीनमा देखाएको यो कुण्डली चक्र/डिग्री र मैले पठाएका कुण्डलीका फोटोहरू दाँजेर शुद्धिकरण गरिदिनुहोस्।
२. मेरा दुवै हातका रेखाहरू र यो कुण्डली मिलाई सिधै विक्रम संवत् (वि.सं.) को महिना/वर्ष तोकेर कारणसहित प्रारम्भिक फलादेश दिनुहोस्।"""
            }
        ]

        if chart_files:
            for c_file in chart_files:
                b64 = optimize_and_encode_image(c_file)
                if b64:
                    user_content.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}})

        if palm_files:
            for p_file in palm_files:
                b64 = optimize_and_encode_image(p_file)
                if b64:
                    user_content.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}})

        client = Groq(api_key=groq_api_key)
        with st.spinner("गुरुजीले चक्र, डिग्री र हस्तरेखा मिलाउँदै हुनुहुन्छ..."):
            try:
                response = client.chat.completions.create(
                    model=GROQ_VISION_MODEL,
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": user_content}
                    ],
                    temperature=0.6,
                    max_tokens=2048
                )
                guru_reply = response.choices[0].message.content
                st.session_state.messages = [
                    {"role": "user", "content": f"प्रणाम गुरुज्यू, मेरो कुण्डली चक्र (लग्न: {lagna_rashi}, राशि: {moon_rashi}) र हात हेरिदिनुहोस्।", "time": datetime.now().strftime("%I:%M %p")},
                    {"role": "assistant", "content": guru_reply, "time": datetime.now().strftime("%I:%M %p")}
                ]
            except Exception as e:
                # यदि मोडल समस्या आएमा fallback
                try:
                    response = client.chat.completions.create(
                        model="meta-llama/llama-4-scout-17b-16e-instruct",
                        messages=[
                            {"role": "system", "content": SYSTEM_PROMPT},
                            {"role": "user", "content": user_content}
                        ],
                        temperature=0.6,
                        max_tokens=2048
                    )
                    guru_reply = response.choices[0].message.content
                    st.session_state.messages = [
                        {"role": "user", "content": f"प्रणाम गुरुज्यू, मेरो कुण्डली चक्र (लग्न: {lagna_rashi}, राशि: {moon_rashi}) र हात हेरिदिनुहोस्।", "time": datetime.now().strftime("%I:%M %p")},
                        {"role": "assistant", "content": guru_reply, "time": datetime.now().strftime("%I:%M %p")}
                    ]
                except Exception as e2:
                    st.error(f"त्रुटि: {str(e2)}")

# --- Render WhatsApp Chat Messages ---
st.markdown('<div class="chat-container">', unsafe_allow_html=True)
for msg in st.session_state.messages:
    t = msg.get("time", "")
    if msg["role"] == "user":
        st.markdown(f'''
        <div class="user-bubble">
            <div>{msg["content"]}</div>
            <div class="msg-time">{t} ✓✓</div>
        </div>
        ''', unsafe_allow_html=True)
    else:
        st.markdown(f'''
        <div class="guru-bubble">
            <div class="sender-name">पूज्य ज्योतिषाचार्य</div>
            <div>{msg["content"]}</div>
            <div class="msg-time">{t}</div>
        </div>
        ''', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

# --- Chat Input (WhatsApp Style) ---
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
                    api_messages = [{"role": "system", "content": SYSTEM_PROMPT}]
                    for m in st.session_state.messages:
                        api_messages.append({"role": m["role"], "content": m["content"]})
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
