import streamlit as st
import base64
import math
from datetime import datetime
from PIL import Image
from groq import Groq

# Page Setup
st.set_page_config(page_title="ज्योतिष गुरु - WhatsApp Chat", page_icon="🟢", layout="wide")

# --- Custom WhatsApp CSS Styling ---
st.markdown("""
<style>
    /* WhatsApp Background */
    .stApp {
        background-color: #efeae2;
    }
    
    /* WhatsApp Top Header Bar */
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
        width: 44px;
        height: 44px;
        border-radius: 50%;
        background-color: #dfdfdf;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 22px;
    }
    .wa-header-info h4 {
        margin: 0;
        color: white;
        font-size: 17px;
    }
    .wa-header-info p {
        margin: 0;
        font-size: 12px;
        color: #d1f7e0;
    }

    /* WhatsApp Chat Bubbles */
    .chat-container {
        display: flex;
        flex-direction: column;
        gap: 10px;
        padding: 10px;
    }
    .user-bubble {
        align-self: flex-end;
        background-color: #d9fdd3;
        color: #111b21;
        padding: 10px 14px;
        border-radius: 12px 0 12px 12px;
        max-width: 80%;
        font-size: 15px;
        box-shadow: 0 1px 2px rgba(0,0,0,0.15);
        word-wrap: break-word;
        line-height: 1.5;
    }
    .guru-bubble {
        align-self: flex-start;
        background-color: #ffffff;
        color: #111b21;
        padding: 12px 16px;
        border-radius: 0 12px 12px 12px;
        max-width: 85%;
        font-size: 15px;
        box-shadow: 0 1px 2px rgba(0,0,0,0.15);
        word-wrap: break-word;
        line-height: 1.6;
    }
    .sender-name {
        font-weight: bold;
        font-size: 11px;
        color: #075e54;
        margin-bottom: 3px;
    }
    .msg-time {
        font-size: 10px;
        color: #667781;
        text-align: right;
        margin-top: 4px;
    }
</style>
""", unsafe_allow_html=True)

# --- Mathematical Engine for Degree & Lahiri Ayanamsha ---
def get_julian_day(year, month, day, hour=0):
    if month <= 2:
        year -= 1
        month += 12
    A = math.floor(year / 100)
    B = 2 - A + math.floor(A / 4)
    jd = math.floor(365.25 * (year + 4716)) + math.floor(30.6001 * (month + 1)) + day + B - 1524.5
    jd += hour / 24.0
    return jd

def calculate_lahiri_ayanamsha(jd):
    T = (jd - 2451545.0) / 36525.0
    return 23.85 + (1.396 * T)

def calculate_approx_vedic_chart(dob, tob_hour, tob_min, lon=85.3240):
    total_hour = tob_hour + (tob_min / 60.0) - 5.75 # UTC Nepal (+5:45)
    jd = get_julian_day(dob.year, dob.month, dob.day, total_hour)
    ayanamsha = calculate_lahiri_ayanamsha(jd)
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
    lagna_long = lst

    chart = {
        "लग्न (Lagna)": to_vedic(lagna_long),
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

def encode_image(uploaded_file):
    if uploaded_file is not None:
        return base64.b64encode(uploaded_file.getvalue()).decode('utf-8')
    return None

# --- Strict Vedic Prompt for Nepali Language & Chart Comparison ---
SYSTEM_PROMPT = """
तपाईं नेपालको परम्परागत वैदिक ज्योतिष तथा सामुद्रिक हस्तरेखा शास्त्रका परम विद्वान 'ज्योतिषाचार्य' हुनुहुन्छ।

मुख्य कार्यसम्पादन नियमहरू:
१. भाषा शैली:
   - तपाईंले सदैव शुद्ध, आदरार्थी, र स्पष्ट नेपाली भाषा (देवनागरी लिपि) मा संवाद गर्नुपर्छ।
   - प्रयोगकर्ताले रोमन नेपाली (Roman Nepali) मा प्रश्न सोधे पनि तपाईंको जवाफ अनिवार्य रूपमा शुद्ध नेपालीमै हुनुपर्छ।

२. कुण्डली शुद्धिकरण तथा तुलना (Cross-Verification Step):
   - सिस्टमले निकालेको गणितीय डिग्री र प्रयोगकर्ताले पठाएको कुण्डलीको फोटोलाई आपसमा दाँज्नुहोस्।
   - यदि फोटोको कुण्डली र गणनामा कुनै ग्रहको भाव वा राशिमा फरक भेटियो भने, कुण्डलीको फोटोलाई नै प्रामाणिक मान्नुहोस् र सो कुरा स्पष्ट उल्लेख गर्नुहोस् ताकि कुनै गल्ती नहोस्।

३. हस्तरेखा समन्वय (Palmistry):
   - हातको फोटोबाट जीवन रेखा, मस्तिष्क रेखा, हृदय रेखा, भाग्य रेखा, र पर्वतहरूको अध्ययन गर्नुहोस्।
   - कुण्डलीका ग्रहहरूको फल र हातका रेखाहरूलाई एकसाथ जोडेर अचुक मार्गदर्शन दिनुहोस्।

४. निरन्तर संवाद (WhatsApp Style Chat):
   - प्रयोगकर्तालाई जुनसुकै प्रश्न (करियर, विदेश यात्रा, धन, विवाह, प्रेम, स्वास्थ्य, उपाय/पूजा) सोध्न दिनुहोस् र आत्मीयताका साथ समाधान दिनुहोस्।
"""

# --- Sidebar Inputs ---
with st.sidebar:
    st.header("⚙️ सेटिङ तथा विवरण")
    groq_api_key = st.text_input("Groq API Key हाल्नुहोस्:", type="password", help="console.groq.com बाट नि:शुल्क पाइन्छ")
    
    st.markdown("---")
    st.subheader("📋 जन्म विवरण")
    dob = st.date_input("जन्म मिति (Date of Birth):", min_value=datetime(1950, 1, 1), max_value=datetime.today())
    tob = st.time_input("जन्म समय (Birth Time):")
    place = st.text_input("जन्म स्थान (City / District):", value="काठमाडौँ, नेपाल")
    
    gender = st.selectbox("लिङ्ग (Gender):", ["पुरुष (Male)", "महिला (Female)", "अन्य"])
    dominant_hand = st.selectbox("सक्रिय हात (Dominant Hand):", ["दाहिने हात (Right Hand)", "देब्रे हात (Left Hand)"])

    st.markdown("---")
    st.subheader("📸 फोटो अपलोड")
    chart_file = st.file_uploader("१. कुण्डलीको फोटो (Nepali Patro/Chart)", type=["jpg", "jpeg", "png"])
    palm_file = st.file_uploader("२. हातको फोटो (Palm Photo)", type=["jpg", "jpeg", "png"])

    past_event = st.text_input("कुनै विगतको मुख्य घटना (समय जाँचको लागि):", placeholder="उदाहरण: २०७८ मा नयाँ जागिर सुरु")

    start_chat = st.button("🟢 कुराकानी सुरु गर्नुहोस्", use_container_width=True)

# --- WhatsApp Header on Main Screen ---
st.markdown("""
<div class="wa-header">
    <div class="wa-avatar">🧘‍♂️</div>
    <div class="wa-header-info">
        <h4>पूज्य ज्योतिषाचार्य (गुरुजी)</h4>
        <p>🟢 अनलाइन | वैदिक ज्योतिष तथा हस्तरेखा विशेषज्ञ</p>
    </div>
</div>
""", unsafe_allow_html=True)

# Session Messages
if "messages" not in st.session_state:
    st.session_state.messages = []

# When Start Chat is clicked
if start_chat:
    if not groq_api_key:
        st.error("कृपया पहिले साइडबारमा Groq API Key हाल्नुहोस्!")
    else:
        chart_data, birth_dasha = calculate_approx_vedic_chart(dob, tob.hour, tob.minute)
        
        degree_summary = f"--- कम्प्युटर गणना कुण्डली डिग्री ---\nजन्म मिति: {dob}, समय: {tob}, स्थान: {place}\n"
        degree_summary += f"लिङ्ग: {gender}, सक्रिय हात: {dominant_hand}\n"
        degree_summary += f"जन्म महादशा स्वामी: {birth_dasha}\n"
        degree_summary += f"विगतको घटना: {past_event}\n"
        for planet, (rashi, deg) in chart_data.items():
            degree_summary += f"{planet}: {rashi} ({deg:.2f}°)\n"

        palm_b64 = encode_image(palm_file)
        chart_b64 = encode_image(chart_file)

        user_content = [
            {
                "type": "text", 
                "text": f"""प्रणाम गुरुज्यू! 
मेरो जन्म विवरण र ग्रहको डिग्री यस प्रकार छ:
{degree_summary}

कृपया:
१. सिस्टमको डिग्री र मैले पठाएको कुण्डलीको फोटोलाई दाँजेर (Cross-check) कुनै फरक भए शुद्धिकरण गर्नुहोस्।
२. मेरो हातको रेखा र कुण्डलीको विश्लेषण गरी समग्र ग्रह स्थिति र फलादेश शुद्ध नेपाली भाषामा दिनुहोस्।
अब हामी ह्वाट्सएपमा जस्तै कुराकानी गर्नेछौँ।"""
            }
        ]

        if chart_b64:
            user_content.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{chart_b64}"}})
        if palm_b64:
            user_content.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{palm_b64}"}})

        client = Groq(api_key=groq_api_key)
        with st.spinner("गुरुजीले कुण्डली र हस्तरेखा अध्ययन गर्दै हुनुहुन्छ..."):
            try:
                response = client.chat.completions.create(
                    model="llama-3.2-11b-vision-preview",
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": user_content}
                    ],
                    temperature=0.7,
                    max_tokens=2048
                )
                guru_reply = response.choices[0].message.content
                st.session_state.messages = [
                    {"role": "user", "content": "प्रणाम गुरुज्यू, मेरो कुण्डली र हातको रेखा हेरिदिनुहोस्।", "time": datetime.now().strftime("%I:%M %p")},
                    {"role": "assistant", "content": guru_reply, "time": datetime.now().strftime("%I:%M %p")}
                ]
            except Exception as e:
                st.error(f"त्रुटि (Error): {str(e)}")

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
if user_question := st.chat_input("यहाँ सन्देश लेख्नुहोस् (उदा: मेरो विदेश यात्रा वा विवाहको योग कहिले छ?)..."):
    if not groq_api_key:
        st.warning("कृपया पहिले साइडबारमा Groq API Key हाल्नुहोस्!")
    else:
        current_time = datetime.now().strftime("%I:%M %p")
        st.session_state.messages.append({"role": "user", "content": user_question, "time": current_time})

        client = Groq(api_key=groq_api_key)
        with st.spinner("गुरुजी लेख्दै हुनुहुन्छ... (typing...)"):
            try:
                api_messages = [{"role": "system", "content": SYSTEM_PROMPT}]
                for m in st.session_state.messages:
                    api_messages.append({"role": m["role"], "content": m["content"]})

                response = client.chat.completions.create(
                    model="llama-3.2-11b-vision-preview",
                    messages=api_messages,
                    temperature=0.7,
                    max_tokens=1500
                )
                reply = response.choices[0].message.content
                st.session_state.messages.append({"role": "assistant", "content": reply, "time": datetime.now().strftime("%I:%M %p")})
                st.rerun()
            except Exception as e:
                st.error(f"त्रुटि: {str(e)}")
