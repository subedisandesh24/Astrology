import streamlit as st
import base64
from datetime import datetime, time
import io
from PIL import Image, ImageFile
from groq import Groq

ImageFile.LOAD_TRUNCATED_IMAGES = True

# Page Setup
st.set_page_config(page_title="भुवनेश्वर सुवेदी - चिना तथा हस्तरेखा विश्लेषण", page_icon="🟢", layout="wide")

# --- Custom WhatsApp CSS Styling ---
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
        font-size: 15px; box-shadow: 0 1px 2px rgba(0,0,0,0.15); word-wrap: break-word; line-height: 1.5;
    }
    .guru-bubble {
        align-self: flex-start; background-color: #ffffff; color: #111b21;
        padding: 12px 16px; border-radius: 0 12px 12px 12px; max-width: 85%;
        font-size: 15px; box-shadow: 0 1px 2px rgba(0,0,0,0.15); word-wrap: break-word; line-height: 1.6;
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

# चिना अनुसार ठ्याक्कै कुण्डली चक्र बनाउने (North Indian Diamond Chart)
def render_verified_china_chart():
    svg = """
    <svg width="100%" height="340" viewBox="0 0 400 400" style="background:#fffaf0; border:2px solid #8b4513; border-radius:8px;">
        <rect x="10" y="10" width="380" height="380" fill="none" stroke="#8b4513" stroke-width="2"/>
        <line x1="10" y1="10" x2="390" y2="390" stroke="#8b4513" stroke-width="1.5"/>
        <line x1="10" y1="390" x2="390" y2="10" stroke="#8b4513" stroke-width="1.5"/>
        <polygon points="200,10 390,200 200,390 10,200" fill="none" stroke="#8b4513" stroke-width="2"/>
        
        <!-- House 1 (कर्कट लग्न) -->
        <text x="200" y="65" font-size="14" fill="#b22222" text-anchor="middle" font-weight="bold">४</text>
        <text x="200" y="105" font-size="13" fill="#666" text-anchor="middle">१ (लग्न)</text>
        
        <!-- House 2 (सिंह) -->
        <text x="100" y="45" font-size="13" fill="#b22222" text-anchor="middle">५</text>
        
        <!-- House 3 (कन्या) -->
        <text x="45" y="100" font-size="13" fill="#b22222" text-anchor="middle">६</text>
        
        <!-- House 4 (तुला) -->
        <text x="90" y="200" font-size="14" fill="#b22222" text-anchor="middle">७</text>
        
        <!-- House 5 (वृश्चिक) -->
        <text x="45" y="300" font-size="13" fill="#b22222" text-anchor="middle">८</text>
        
        <!-- House 6 (धनु - चन्द्र + केतु) -->
        <text x="100" y="355" font-size="13" fill="#b22222" text-anchor="middle">९</text>
        <text x="125" y="315" font-size="14" fill="#075e54" text-anchor="middle" font-weight="bold">चं के</text>
        
        <!-- House 7 (मकर) -->
        <text x="200" y="340" font-size="14" fill="#b22222" text-anchor="middle">१०</text>
        
        <!-- House 8 (कुम्भ) -->
        <text x="300" y="355" font-size="13" fill="#b22222" text-anchor="middle">११</text>
        
        <!-- House 9 (मीन - शुक्र उच्च) -->
        <text x="355" y="300" font-size="13" fill="#b22222" text-anchor="middle">१२</text>
        <text x="330" y="270" font-size="14" fill="#075e54" text-anchor="middle" font-weight="bold">शु (उच्च)</text>
        
        <!-- House 10 (मेष - ५ ग्रह: सूर्य, मंगल, बुध, गुरु, शनि) -->
        <text x="310" y="200" font-size="14" fill="#b22222" text-anchor="middle">१</text>
        <text x="260" y="195" font-size="13" fill="#075e54" text-anchor="middle" font-weight="bold">सू मं बु</text>
        <text x="260" y="215" font-size="13" fill="#075e54" text-anchor="middle" font-weight="bold">गु श</text>
        
        <!-- House 11 (वृषभ) -->
        <text x="355" y="100" font-size="13" fill="#b22222" text-anchor="middle">२</text>
        
        <!-- House 12 (मिथुन - राहु) -->
        <text x="300" y="45" font-size="13" fill="#b22222" text-anchor="middle">३</text>
        <text x="280" y="80" font-size="14" fill="#075e54" text-anchor="middle" font-weight="bold">रा</text>
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

तपाईंको अगाडि प्रयोगकर्ता श्री भुवनेश्वर सुवेदीको आधिकारिक जन्मपत्रिका (चिना) को विवरण छ:
- जन्म: वि.सं. २०५७ बैशाख १२ गते, दिउँसो १:२५ बजे, पुतलीबजार, स्याङ्जा।
- लग्न: कर्कट लग्न (१३° २३')
- राशि: धनु राशि (११° २०')
- नक्षत्र: पूर्वाषाढा नक्षत्र (प्रथम चरण), नामाक्षर: 'भू'
- दशा: जन्ममा शुक्र महादशा थियो, हाल २०७९ मंसिरदेखि २०८९ मंसिरसम्म "चन्द्रमाको महादशा" चल्दैछ।
- मुख्य योगहरू: १०औँ भाव (कर्म) मा सूर्य, मंगल, बुध, गुरु र शनिको महा-पञ्चग्रही राजयोग छ। ९औँ भावमा शुक्र उच्च छ।

नियमहरू:
१. अब कुनै पनि ग्रह वा लग्नको हिसाबमा द्विविधा नगर्नुहोस्। यो चिना प्रमाणित भइसकेको छ।
२. प्रयोगकर्ताले पठाएका हातका तस्बिरहरू (दाहिने र देब्रे) र यो कुण्डलीलाई जोडेर वि.सं. को वर्ष र महिना तोकी कारणसहित फलादेश दिनुहोस्।
३. च्याटको क्रममा विषय परिवर्तन (करियर, विवाह, विदेश, धन, स्वास्थ्य) भएमा सोही अनुसार सटीक मार्गदर्शन गर्नुहोस्।
४. सधैं शुद्ध, आदरार्थी, र स्पष्ट नेपाली भाषा (देवनागरी लिपि) मा जवाफ दिनुहोस्।
"""

# --- Sidebar Inputs ---
with st.sidebar:
    st.markdown("### 📜 प्रमाणित जन्म विवरण (चिना अनुसार)")
    st.success("✅ चिनाबाट प्रमाणित भइसकेको विवरण:")
    
    st.markdown("""
    * **नाम:** श्री भुवनेश्वर सुवेदी
    * **जन्म मिति:** वि.सं. २०५७ बैशाख १२ (सोमबार)
    * **जन्म समय:** दिउँसो १:२५ बजे
    * **स्थान:** पुतलीबजार, स्याङ्जा
    * **लग्न:** कर्कट लग्न (अङ्क ४)
    * **राशि:** धनु राशि (अङ्क ९)
    * **नक्षत्र:** पूर्वाषाढा (चरण १)
    * **वर्तमान महादशा:** चन्द्र महादशा (२०७९-२०८९)
    """)

    st.markdown("---")
    st.markdown("### 📸 हातको फोटो अपलोड")
    palm_files = st.file_uploader("हातका फोटोहरू (दाहिने र देब्रे दुवै हाल्न सक्नुहुन्छ):", type=["jpg", "jpeg", "png"], accept_multiple_files=True)

    default_key = st.secrets.get("GROQ_API_KEY", "")
    if not default_key:
        groq_api_key = st.text_input("Groq Key:", type="password")
    else:
        groq_api_key = default_key

    start_chat = st.button("🟢 चिना र हात हेरी कुराकानी सुरु गर्नुहोस्", use_container_width=True)

# --- Header ---
st.markdown("""
<div class="wa-header">
    <div class="wa-avatar">🧘‍♂️</div>
    <div class="wa-header-info">
        <h4>पूज्य ज्योतिषाचार्य (गुरुजी)</h4>
        <p>🟢 अनलाइन | चिना प्रमाणित: कर्कट लग्न, धनु राशि, पूर्वाषाढा नक्षत्र</p>
    </div>
</div>
""", unsafe_allow_html=True)

# --- प्रमाणित कुण्डली चक्र र विवरण कार्ड ---
st.markdown('<div class="kundali-card">', unsafe_allow_html=True)
st.subheader("🪐 चिना अनुसारको प्रमाणित लग्न कुण्डली चक्र")

col_k1, col_k2 = st.columns([1.1, 1])

with col_k1:
    st.markdown(render_verified_china_chart(), unsafe_allow_html=True)

with col_k2:
    st.markdown("""
    * **जन्म नाम:** **श्री भुवनेश्वर सुवेदी** (नामाक्षर: **भू**)
    * **लग्न (Ascendant):** **कर्कट (अङ्क ४)** — `१३° २३'`
    * **जन्म राशि (Moon Sign):** **धनु (अङ्क ९)** — `११° २०'`
    * **जन्म नक्षत्र:** **पूर्वाषाढा** (प्रथम चरण)
    * **वर्तमान महादशा:** **चन्द्रमाको महादशा** (वि.सं. २०७९ मंसिर - २०८९ मंसिर)
    """)
    st.markdown("---")
    st.markdown("**चिना अनुसार ग्रह स्थिति:**")
    st.write("• **दशम भाव (मेष):** सूर्य (उच्च/दिग्बली), मंगल, बुध, गुरु, शनि (५ ग्रह राजयोग)")
    st.write("• **नवम भाव (मीन):** शुक्र (परम उच्च २८° ३५')")
    st.write("• **षष्ठ भाव (धनु):** चन्द्र + केतु")
    st.write("• **द्वादश भाव (मिथुन):** राहु")
st.markdown('</div>', unsafe_allow_html=True)

if "messages" not in st.session_state:
    st.session_state.messages = []

# When Chat is clicked
if start_chat:
    if not groq_api_key:
        st.error("कृपया Groq API Key हाल्नुहोस्!")
    else:
        user_content = [
            {
                "type": "text", 
                "text": """प्रणाम गुरुज्यू! 
मेरो वास्तविक चिनाको विवरण यस प्रकार छ:
- नाम: श्री भुवनेश्वर सुवेदी, जन्म मिति: वि.सं. २०५७ बैशाख १२ गते, दिउँसो १:२५ बजे, पुतलीबजार, स्याङ्जा।
- कर्कट लग्न (१३° २३'), धनु राशि (११° २०'), पूर्वाषाढा नक्षत्र (चरण १)।
- १०औँ भावमा सूर्य, मंगल, बुध, गुरु र शनिको पञ्चग्रही योग तथा ९औँ भावमा शुक्र उच्च छ।
- हाल चन्द्रमाको महादशा चलिरहेको छ।

मैले मेरो हातका तस्बिरहरू संलग्न गरेको छु। कृपया यो प्रमाणित कुण्डली र हातका रेखाहरू मिलाएर सिधै विक्रम संवत् (वि.सं.) को वर्ष र महिना तोकेर कारणसहित मेरो प्रारम्भिक फलादेश शुद्ध नेपालीमा दिनुहोस्।"""
            }
        ]

        if palm_files:
            for p_file in palm_files:
                b64 = optimize_and_encode_image(p_file)
                if b64: user_content.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}})

        client = Groq(api_key=groq_api_key)
        with st.spinner("गुरुजीले प्रमाणित चिना र हस्तरेखा अध्ययन गर्दै हुनुहुन्छ..."):
            try:
                response = client.chat.completions.create(
                    model=GROQ_VISION_MODEL,
                    messages=[{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": user_content}],
                    temperature=0.6,
                    max_tokens=2048
                )
                guru_reply = response.choices[0].message.content
                st.session_state.messages = [
                    {"role": "user", "content": "प्रणाम गुरुज्यू, मेरो प्रमाणित चिना (कर्कट लग्न, धनु राशि) र हात हेरिदिनुहोस्।", "time": datetime.now().strftime("%I:%M %p")},
                    {"role": "assistant", "content": guru_reply, "time": datetime.now().strftime("%I:%M %p")}
                ]
            except Exception as e:
                try:
                    response = client.chat.completions.create(
                        model="meta-llama/llama-4-scout-17b-16e-instruct",
                        messages=[{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": user_content}],
                        temperature=0.6,
                        max_tokens=2048
                    )
                    guru_reply = response.choices[0].message.content
                    st.session_state.messages = [
                        {"role": "user", "content": "प्रणाम गुरुज्यू, मेरो प्रमाणित चिना र हात हेरिदिनुहोस्।", "time": datetime.now().strftime("%I:%M %p")},
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

# --- Interactive WhatsApp Chat Input ---
if user_question := st.chat_input("यहाँ सन्देश लेख्नुहोस् (कुनै पनि विषय: करियर, विदेश, विवाह, धन...)..."):
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
