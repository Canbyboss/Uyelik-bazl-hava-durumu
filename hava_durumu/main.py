import streamlit as st
import requests
import sqlite3
import datetime
import pandas as pd
from hashlib import sha256

# Veritabanı Bağlantısı
conn = sqlite3.connect('weather.db', check_same_thread=False)
c = conn.cursor()

# Tabloların Oluşturulması
c.execute('''
    CREATE TABLE IF NOT EXISTS users (
        username TEXT PRIMARY KEY,
        password TEXT
    )
''')
c.execute('''
    CREATE TABLE IF NOT EXISTS queries (
        username TEXT,
        city TEXT,
        temperature REAL,
        condition TEXT,
        date TEXT
    )
''')
conn.commit()


# Kullanıcı Kaydı ve Giriş Fonksiyonları
def register_user(username, password):
    hashed_password = sha256(password.encode()).hexdigest()
    try:
        c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed_password))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False


def login_user(username, password):
    hashed_password = sha256(password.encode()).hexdigest()
    c.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, hashed_password))
    return c.fetchone() is not None


def save_query_to_db(username, city, temp, condition):
    date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute("INSERT INTO queries (username, city, temperature, condition, date) VALUES (?, ?, ?, ?, ?)",
              (username, city, temp, condition, date))
    conn.commit()


def get_past_queries():
    if 'username' in st.session_state:
        username = st.session_state['username']
        c.execute("SELECT city, temperature, condition, date FROM queries WHERE username = ?", (username,))
        return c.fetchall()
    return []


def get_weather_data(city):
    api_key = '2031fbdfa5234eeba51115732240709'
    url = f"http://api.weatherapi.com/v1/current.json?key={api_key}&q={city}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    return None


# Çıkış Yapma Fonksiyonu
def logout_user():
    if 'logged_in' in st.session_state:
        del st.session_state['logged_in']
    if 'username' in st.session_state:
        del st.session_state['username']
    st.session_state['logged_in'] = False  # Kullanıcıyı çıkış yapmış olarak işaretleyin
    st.session_state['username'] = ""  # Kullanıcı adını temizleyin


# HTML ve CSS ile Görselleştirme
st.markdown("""
    <style>
    .main-title {
        font-size: 48px;
        font-weight: bold;
        color: #4a90e2;
        text-align: center;
        margin-top: 20px;
        margin-bottom: 20px;
    }
    .description {
        font-size: 24px;
        color: #333;
        text-align: center;
        margin-bottom: 40px;
    }
    .container {
        padding: 20px;
        background-color: #f5f5f5;
        border-radius: 10px;
        box-shadow: 0 5px 15px rgba(0, 0, 0, 0.2);
    }
    .button {
        background-color: #4a90e2;
        color: white;
        padding: 12px 24px;
        border-radius: 8px;
        text-align: center;
        font-size: 18px;
        cursor: pointer;
        border: none;
    }
    .button:hover {
        background-color: #357abd;
    }
    .button-danger {
        background-color: #e94e77;
        color: white;
    }
    .button-danger:hover {
        background-color: #c83e5c;
    }
    .weather-icon {
        transition: transform 0.3s ease;
    }
    .weather-icon:hover {
        transform: scale(1.2);
    }
    .sidebar-title {
        font-size: 24px;
        color: #4a90e2;
        margin-bottom: 20px;
    }
    .form-input {
        margin-bottom: 10px;
    }
    .warning {
        color: #e94e77;
        font-size: 14px;
        font-style: italic;
    }
    </style>
    """, unsafe_allow_html=True)

st.markdown('<p class="main-title">Hava Durumu Uygulaması</p>', unsafe_allow_html=True)
st.markdown(
    '<p class="description">Şehir ismini girerek hava durumu bilgilerini öğrenebilirsiniz. (İngilizce karakter kullanın)</p>',
    unsafe_allow_html=True)

# Üyelik Sistemi Arayüzü
st.sidebar.markdown("""
    <style>
    .sidebar-title {
        font-size: 24px;
        color: #4a90e2;
        margin-bottom: 20px;
    }
    </style>
    """, unsafe_allow_html=True)

st.sidebar.header("Üyelik Sistemi", anchor='sidebar-title')

auth_option = st.sidebar.selectbox("Giriş veya Kayıt", ["Giriş Yap", "Kayıt Ol"], key="auth_option")

if auth_option == "Kayıt Ol":
    st.sidebar.header("Kayıt Ol")
    username = st.sidebar.text_input("Kullanıcı Adı", key="register_username")
    password = st.sidebar.text_input("Şifre", type="password", key="register_password")
    if st.sidebar.button("Kayıt Ol"):
        if username and password:
            if register_user(username, password):
                st.sidebar.success("Kayıt başarılı!")
            else:
                st.sidebar.error("Kullanıcı adı zaten mevcut.")
        else:
            st.sidebar.error("Lütfen tüm alanları doldurun.")

elif auth_option == "Giriş Yap":
    st.sidebar.header("Giriş Yap")
    username = st.sidebar.text_input("Kullanıcı Adı", key="login_username")
    password = st.sidebar.text_input("Şifre", type="password", key="login_password")
    if st.sidebar.button("Giriş Yap"):
        if username and password:
            if login_user(username, password):
                st.session_state['logged_in'] = True
                st.session_state['username'] = username
                st.sidebar.success("Giriş başarılı!")
            else:
                st.sidebar.error("Kullanıcı adı veya şifre hatalı.")
        else:
            st.sidebar.error("Lütfen tüm alanları doldurun.")

# Çıkış Yapma Butonu
if 'logged_in' in st.session_state and st.session_state['logged_in']:
    st.sidebar.button("Çıkış Yap", on_click=logout_user)

    city = st.text_input("Şehir ismini girin:", "")
    if city:
        weather_data = get_weather_data(city)
        if weather_data:
            temp = weather_data['current']['temp_c']
            condition = weather_data['current']['condition']['text']
            icon_url = weather_data['current']['condition']['icon']

            st.markdown(f'<img src="http:{icon_url}" class="weather-icon" width="100">', unsafe_allow_html=True)
            st.write(f"Sıcaklık: {temp}°C")
            st.write(f"Durum: {condition}")

            save_query_to_db(st.session_state['username'], city, temp, condition)
            st.write("Veriler kaydedildi.")
        else:
            st.write("Hava durumu bilgisi getirilemedi.")

    if st.button("Geçmiş sorguları göster"):
        past_queries = get_past_queries()
        if past_queries:
            df = pd.DataFrame(past_queries, columns=["Şehir", "Sıcaklık (°C)", "Durum", "Tarih"])
            st.dataframe(df)  # Geçmiş sorguları tablo olarak göster
        else:
            st.write("Henüz sorgu yapılmamış.")

else:
    st.info("Lütfen giriş yapın veya kayıt olun.")
# canberk  - 123 DENEME ÜYELİKLER
# CANBERK - 123 DENEME ÜYELİKLER