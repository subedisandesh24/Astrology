import streamlit as st
import base64
import math
from datetime import datetime
from PIL import Image
import io
from groq import Groq

# Page Setup
st.set_page_config(page_title="ज्योतिष गुरु - WhatsApp Chat", page_icon="🟢", layout="wide")

# --- Custom WhatsApp CSS Styling ---
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
</style>
""", unsafe_allow_html=True)

# --- BS to AD Approximate Conversion Engine ---
def bs_to_ad_approx(bs_year, bs_month, bs_day):
    ad_year = bs_year - 56 if bs_month >= 9 else bs_year - 57
    ad_month = (bs_month + 8) % 12
    if ad_month == 0: ad_month = 12
    ad_day = (bs_day + 13) % 30
    if ad_day == 0: ad_day = 1
    return ad_year, ad_month, ad_day

# --- Mathematical Degree Calculation (Vedic/Lahiri) ---
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
    total_hour = tob_hour + (tob_min / 60.0) - 5.75 # UTC Nepal
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
        return rashis[rashi_idx], degree_in_rashi

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

    moon_vedic_deg = (moon_long - ayanamsha) % 360
    nakshatra_idx = int(moon_vedic_deg // 13.333333)
    dasha_lords = ["केतु", "शुक्र", "सूर्य", "चन्द्र", "मंगल", "राहु", "गुरु", "शनि", "बुध"]
    current_birth_lord = dasha_lords[nakshatra_idx % 9]

    return chart, current_birth_lord

def optimize_and_encode_image(uploaded_file):
    """Resizes and compresses images to avoid hitting Groq payload limits"""
    if uploaded_file is not None:
        img = Image.open(uploaded_file)
        if img.mode != "RGB":
            img = img.convert("RGB")
        img.thumbnail((1024, 1024))
        buffer = io.BytesIO()
        img.save(buffer, format="JPEG", quality=85)
        return base64.b64encode(buffer.getvalue()).decode('utf-8')
    return None

# --- Prompt with Dynamic Topic Switching & BS Timeline Reasoning ---
SYSTEM_PROMPT = """
तपाईं नेपालको परम्परागत सिद्धान्त ज्योतिष, फलित ज्योतिष, र सामुद्रिक हस्तरेखा शास्त्रका परम विद्वान 'ज्योतिषाचार्य' हुनुहुन्छ।

मुख्य कार्यसम्पादन नियमहरू:
१. समय र मिति (Strict BS Timeline):
   - कुनै पनि भविष्यवाणी गर्दा अनिवार्य रूपमा नेपाली विक्रम संवत् (वि.सं.) को वर्ष र महिना तोकेर बोल्नुहोस्। (उदा: "२०८३ असार मसान्तभित्र...", "२०८४ कार्तिक देखि २०८५ फागुनसम्म...")।

२. ठोस ज्योतिषीय कारण (Mandatory Astrological Reasoning):
   - फलादेश गर्दा त्यसको पछाडि महादशा, अन्तर्दशा, गोचर, भावको दृष्टि, ग्रहको डिग्री, र हातको सम्बन्धित रेखा/पर्वतको अवस्था अनिवार्य रूपमा खुलाउनुहोस्।

३. बहु-कुण्डली तुलना तथा शुद्धिकरण (Multi-Chart Cross-Verification):
   - प्रयोगकर्ताले पठाएका विभिन्न कुण्डलीका फोटोहरू (लग्न, नवमांश, दशा, चलित) र गणितीय डिग्रीलाई आपसमा तुलना गरी पूर्ण शुद्धिकरण गर्नुहोस्। फोटोको कुण्डलीलाई नै आधिकारिक मान्नुहोस्।

४. विषय परिवर्तन सम्हाल्ने क्षमता (Dynamic Topic Switching):
   - च्याटको क्रममा प्रयोगकर्ताले अचानक विषय परिवर्तन गर्न सक्छन् (जस्तै: जागिरको कुरा गर्दागर्दै सिधै विवाह, विदेश यात्रा, सन्तान, वा स्वास्थ्यमा जान सक्छन्)।
   - यस्तो अवस्थामा कुनै द्विविधा नराखी, नयाँ विषयसँग सम्बन्धित भाव (Ghar), कारक ग्रह, र हातको रेखामा सिधै प्रवेश गरी वि.सं. मिति र कारणसहित जवाफ दिनुहोस्।
   - अघिल्लो प्रसंगलाई बिर्सिनु पर्दैन, तर नयाँ विषयमा पूर्ण ध्यान केन्द्रित गर्नुहोस्।

५. भाषा शैली:
   - प्रयोगकर्ताले रोमन नेपालीमा सोधे पनि तपाईंको सम्पूर्ण सम्वाद शुद्ध, आदरार्थी, र स्पष्ट नेपाली भाषा (देवनागरी लिपि) मै हुनुपर्छ। ह्वाट्सएपमा जस्तै आत्मीय सल्लाह दिनुहोस्।
"""

# --- Sidebar: Direct Birth Details (Bikram Sambat) ---
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
    place = st.text_input("जन्म स्थान (City / District):", value="काठमाडौँ, नेपाल")
    
    col_g, col_h = st.columns(2)
    with col_g:
        gender = st.selectbox("लिङ्ग:", ["पुरुष", "महिला", "अन्य"])
    with col_h:
        dominant_hand = st.selectbox("सक्रिय हात:", ["दाहिने", "देब्रे"])

    st.markdown("---")
    st.markdown("### 📸 फोटोहरू अपलोड")
    # Multiple Kundali Photos Allowed
    chart_files = st.file_uploader(
        "१. कुण्डलीका फोटोहरू (लग्न, नवमांश, दशा आदि - जति पनि हाल्न मिल्ने)", 
        type=["jpg", "jpeg", "png"], 
        accept_multiple_files=True
    )
    palm_file = st.file_uploader("२. हातको फोटो (Palm Photo)", type=["jpg", "jpeg", "png"])

    past_event = st.text_input("विगतको मुख्य घटना (समय जाँच्न):", placeholder="उदा: २०७८ मा जागिर सुरु")

    default_key = st.secrets.get("GROQ_API_KEY", "")
    if not default_key:
        groq_api_key = st.text_input("Groq Key (एकपटकको लागि):", type="password")
    else:
        groq_api_key = default_key

    start_chat = st.button("🟢 कुराकानी सुरु गर्नुहोस्", use_container_width=True)

# --- WhatsApp Header on Main Screen ---
st.markdown("""
<div class="wa-header">
    <div class="wa-avatar">🧘‍♂️</div>
    <div class="wa-header-info">
        <h4>पूज्य ज्योतिषाचार्य (गुरुजी)</h4>
        <p>🟢 अनलाइन | वि.सं. अनुसार मिति, बहु-कुण्डली विश्लेषण र विषय परिवर्तन सक्षम</p>
    </div>
</div>
""", unsafe_allow_html=True)

if "messages" not in st.session_state:
    st.session_state.messages = []

# When Start Chat is clicked
if start_chat:
    if not groq_api_key:
        st.error("कृपया Groq API Key हाल्नुहोस्!")
    else:
        ad_y, ad_m, ad_d = bs_to_ad_approx(bs_year, bs_month, bs_day)
        chart_data, birth_dasha = calculate_approx_vedic_chart(ad_y, ad_m, ad_d, tob.hour, tob.minute)
        
        degree_summary = f"--- जन्म विवरण ---\nजन्म मिति: वि.सं. {bs_year}/{bs_month}/{bs_day}, समय: {tob}, स्थान: {place}\n"
        degree_summary += f"लिङ्ग: {gender}, सक्रिय हात: {dominant_hand}\n"
        degree_summary += f"जन्म महादशा स्वामी: {birth_dasha}\n"
        degree_summary += f"विगतको घटना: {past_event}\n"
        for planet, (rashi, deg) in chart_data.items():
            degree_summary += f"{planet}: {rashi} ({deg:.2f}°)\n"

        user_content = [
            {
                "type": "text", 
                "text": f"""प्रणाम गुरुज्यू! 
मेरो वि.सं. जन्म विवरण यस प्रकार छ:
{degree_summary}

मैले मेरो कुण्डलीका फोटोहरू र हातको फोटो संलग्न गरेको छु। कृपया:
१. सिस्टमको डिग्री र संलग्न सबै कुण्डलीका फोटोहरू (लग्न, नवमांश, दशा आदि) दाँजेर शुद्धिकरण गर्नुहोस्।
२. हातको रेखा र कुण्डलीको आधारमा वि.सं. को महिना/वर्ष तोकेर कारणसहित प्रारम्भिक फलादेश दिनुहोस्।"""
            }
        ]

        # Append all uploaded Kundali images
        if chart_files:
            for idx, c_file in enumerate(chart_files):
                b64 = optimize_and_encode_image(c_file)
                if b64:
                    user_content.append({
                        "type": "image_url", 
                        "image_url": {"url": f"data:image/jpeg;base64,{b64}"}
                    })

        # Append palm image
        palm_b64 = optimize_and_encode_image(palm_file)
        if palm_b64:
            user_content.append({
                "type": "image_url", 
                "image_url": {"url": f"data:image/jpeg;base64,{palm_b64}"}
            })

        client = Groq(api_key=groq_api_key)
        with st.spinner("गुरुजीले सबै कुण्डलीका फोटोहरू र हस्तरेखा अध्ययन गर्दै हुनुहुन्छ..."):
            try:
                response = client.chat.completions.create(
                    model="llama-3.2-11b-vision-preview",
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": user_content}
                    ],
                    temperature=0.6,
                    max_tokens=2048
                )
                guru_reply = response.choices[0].message.content
                st.session_state.messages = [
                    {"role": "user", "content": f"प्रणाम गुरुज्यू, मेरो जन्म मिति वि.सं. {bs_year}/{bs_month}/{bs_day} हो। मेरो कुण्डली र हात हेरिदिनुहोस्।", "time": datetime.now().strftime("%I:%M %p")},
                    {"role": "assistant", "content": guru_reply, "time": datetime.now().strftime("%I:%M %p")}
                ]
            except Exception as e:
                st.error(f"त्रुटि: {str(e)}")

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

# --- Chat Input (Handles Dynamic Topic Switching) ---
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
                    model="llama-3.2-11b-vision-preview",
                    messages=api_messages,
                    temperature=0.6,
                    max_tokens=1500
                )
                reply = response.choices[0].message.content
                st.session_state.messages.append({"role": "assistant", "content": reply, "time": datetime.now().strftime("%I:%M %p")})
                st.rerun()
            except Exception as e:
                st.error(f"त्रुटि: {str(e)}")
