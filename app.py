import streamlit as st
import pandas as pd
import json
import os
import base64
from datetime import datetime
import plotly.express as px

# ตั้งค่าหน้า Web App
st.set_page_config(
    page_title="Pro XAUUSD Journal & Analytics",
    page_icon="📈",
    layout="wide"
)

DATA_FILE = "trade_history.json"

def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return []
    return []

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

if "trades" not in st.session_state:
    st.session_state.trades = load_data()

st.title("📈 Pro XAUUSD Journal & Analytics")
st.caption("ระบบวางแผนเทรด บันทึก Mindset ทบทวนกราฟ และวิเคราะห์สถิติการเทรดเชิงลึก")

tab1, tab2, tab3 = st.tabs(["🧮 คำนวณ & บันทึกออเดอร์", "📜 ประวัติ & สำรองข้อมูล", "📊 สรุปผล & Equity Curve"])

# ==========================================
# TAB 1: CALCULATOR & TRADE JOURNAL INPUT
# ==========================================
with tab1:
    st.header("1. คำนวณความเสี่ยงและแผนการเทรด")
    
    col_input, col_result = st.columns([1, 1])
    
    with col_input:
        capital = st.number_input("ทุนในพอร์ตปัจจุบัน ($)", min_value=1.0, value=100.0, step=10.0)
        symbol = st.selectbox("สินทรัพย์", ["XAUUSD (ทองคำ)", "EURUSD", "GBPUSD", "BTCUSD"])
        side = st.radio("ฝั่งการเทรด", ["BUY", "SELL"], horizontal=True)
        
        lot_mode = st.radio("วิธีการกำหนดขนาด Lot", ["กรอกขนาด Lot เอง", "คำนวณ Lot อัตโนมัติจาก % Risk"], horizontal=True)
        entry_price = st.number_input("ราคาเข้า (Entry Price)", min_value=0.0, value=4363.229, format="%.3f")
        calc_mode = st.radio("รูปแบบการกำหนดเป้าหมาย", ["กรอกราคา SL/TP ตรงๆ", "กำหนดจากค่า RR"], horizontal=True)
        
        if calc_mode == "กรอกราคา SL/TP ตรงๆ":
            default_sl = entry_price - 10.0 if side == "BUY" else entry_price + 10.0
            default_tp = entry_price + 20.0 if side == "BUY" else entry_price - 20.0
            sl_price = st.number_input("ราคา Stop Loss (SL)", min_value=0.0, value=default_sl, format="%.3f")
            tp_price = st.number_input("ราคา Take Profit (TP)", min_value=0.0, value=default_tp, format="%.3f")
        else:
            sl_distance = st.number_input("ระยะ SL (ดอลลาร์/จุด)", min_value=0.1, value=3.0, step=0.5)
            rr_target = st.number_input("เป้าหมาย RR (1 : X)", min_value=0.5, value=2.0, step=0.5)
            sl_price = (entry_price - sl_distance) if side == "BUY" else (entry_price + sl_distance)
            tp_price = (entry_price + (sl_distance * rr_target)) if side == "BUY" else (entry_price - (sl_distance * rr_target))
            st.info(f"📍 คำนวณอัตโนมัติ -> SL: {sl_price:.3f} | TP: {tp_price:.3f}")

        sl_dist = (entry_price - sl_price) if side == "BUY" else (sl_price - entry_price)
        tp_dist = (tp_price - entry_price) if side == "BUY" else (entry_price - tp_price)

        if lot_mode == "กรอกขนาด Lot เอง":
            lot = st.number_input("ขนาด Lot Size", min_value=0.01, value=0.01, step=0.01, format="%.2f")
        else:
            risk_percent_input = st.number_input("ยอมเสียได้กี่ % ของพอร์ต", min_value=0.1, max_value=100.0, value=1.0, step=0.5)
            max_risk_usd = (capital * risk_percent_input) / 100.0
            calculated_lot = max_risk_usd / (sl_dist * 100.0) if sl_dist > 0 else 0.01
            lot = max(0.01, round(calculated_lot, 2))
            st.success(f"💡 ขนาด Lot แนะนำ: **{lot:.2f} Lot** (เสี่ยง ${max_risk_usd:.2f})")

    max_loss = sl_dist * (lot * 100)
    max_profit = tp_dist * (lot * 100)
    rr_ratio = tp_dist / sl_dist if sl_dist > 0 else 0
    risk_pct = (max_loss / capital) * 100

    with col_result:
        st.subheader("📊 ผลการคำนวณ")
        res_c1, res_c2 = st.columns(2)
        res_c1.metric("🔴 ขาดทุนสูงสุด (SL)", f"-${max_loss:.2f}", f"{risk_pct:.1f}% ของพอร์ต", delta_color="inverse")
        res_c2.metric("🟢 กำไรสูงสุด (TP)", f"+${max_profit:.2f}", f"{(max_profit/capital)*100:.1f}% ของพอร์ต")
        st.write(f"⚖️ **RR Ratio:** `1 : {rr_ratio:.2f}` | 📏 **ระยะ SL:** {sl_dist*100:.0f} จุด | 🎯 **ระยะ TP:** {tp_dist*100:.0f} จุด")
        
        st.divider()
        st.subheader("🧠 บันทึกบริบทการเทรด (Context & Mindset)")
        
        tag_col1, tag_col2 = st.columns(2)
        with tag_col1:
            setup_list = st.multiselect(
                "รูปแบบการเข้าเทรด (Setup) - เลือกได้หลายข้อ", 
                [
                    "Smart Money Concepts (SMC)", 
                    "Quasimodo (QM)", 
                    "RSI Hidden Divergence", 
                    "Breakout / Retest", 
                    "News Trade (เทรดข่าว)",
                    "อื่นๆ"
                ],
                default=["Smart Money Concepts (SMC)"]
            )
            
            session = st.selectbox(
                "ช่วงเวลาการเทรด (Session)", 
                [
                    "Asian Session (06:00 - 13:00 น.)", 
                    "London Session (14:00 - 22:00 น.)", 
                    "New York Session (19:30 - 03:00 น.)", 
                    "Overlap Session (19:30 - 22:00 น.)"
                ]
            )
            
        with tag_col2:
            mindset = st.selectbox("สภาพจิตใจ / การทำตามแผน", [
                "🟢 นิ่ง / ทำตามแผน 100%", 
                "🟡 FOMO (กลัวตกรถ/เข้าเร็วเกิน)", 
                "🔴 Revenge Trade (เทรดเอาคืน)", 
                "🟠 โลภ / ขยับ TP ไกลขึ้น",
                "⚪ เทรดแก้เบื่อ / นอกแผน"
            ])
            
            uploaded_image = st.file_uploader("📸 อัปโหลดรูปภาพกราฟ (PNG, JPG)", type=["png", "jpg", "jpeg"])
            
        note = st.text_input("บันทึกโน้ตเพิ่มเติม", placeholder="เช่น เกิด M5 Rejection ที่แนวรับ H1")
        
        if st.button("💾 บันทึกออเดอร์นี้ลง Journal", type="primary", use_container_width=True):
            image_base64 = ""
            if uploaded_image is not None:
                bytes_data = uploaded_image.getvalue()
                image_base64 = f"data:image/png;base64,{base64.b64encode(bytes_data).decode('utf-8')}"

            new_id = (max([t["id"] for t in st.session_state.trades]) + 1) if st.session_state.trades else 1
            new_trade = {
                "id": new_id,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "symbol": symbol,
                "side": side,
                "lot": lot,
                "entry": entry_price,
                "sl": sl_price,
                "tp": tp_price,
                "max_loss": round(max_loss, 2),
                "max_profit": round(max_profit, 2),
                "rr": round(rr_ratio, 2),
                "setup": ", ".join(setup_list) if setup_list else "ไม่ได้ระบุ",
                "session": session,
                "mindset": mindset,
                "image_data": image_base64,
                "status": "Active (ถืออยู่)",
                "pnl": 0.0,
                "note": note
            }
            st.session_state.trades.append(new_trade)
            save_data(st.session_state.trades)
            st.success("✅ บันทึกออเดอร์เรียบร้อยแล้ว!")
            st.rerun()

    # ==========================================
    # โซนกรอบคู่มือสรุปความหมาย SETUP & SESSION
    # ==========================================
    st.markdown("<br>", unsafe_allow_html=True)
    with st.expander("📖 **คลิกเพื่อดูคู่มือสรุปความหมาย Setup & Session (Cheat Sheet)**", expanded=True):
        guide_col1, guide_col2 = st.columns(2)
        
        with guide_col1:
            st.markdown("### 🎯 ความหมายของ Setup (รูปแบบเข้าเทรด)")
            st.markdown("""
            * **Smart Money Concepts (SMC):** เทรดตามรอยรายใหญ่/สถาบัน เน้นเข้าซื้อขายบริเวณ **Order Block (OB)**, **Fair Value Gap (FVG)** หรือรอให้เกิดการกวาดสภาพคล่อง (**Liquidity Sweep**) และการเปลี่ยนโครงสร้างราคา (**BOS / CHoCH**)
            * **Quasimodo (QM):** รูปแบบการกลับตัวของราคาที่ทำจุดสูง/ต่ำใหม่ (ทำ HH แล้วทุบทำ LL หรือทำ LL แล้วดันทำ HH) แล้วย่อกลับมาทดสอบโซนไหล่เดิม (**Left Shoulder Zone**) เป็นจุดเข้าเทรดที่มี RR สูง
            * **RSI Hidden Divergence:** สัญญาณเทรดตามเทรนด์เดิมเพื่อหาจุดย่อเข้า เช่น ราคาทำ **Higher Low (HL)** แต่ RSI ทำ **Lower Low (LL)** ในเทรนด์ขาขึ้น 
            * **Breakout / Retest:** ราคาทะลุแนวรับ-แนวต้าน หรือ Trendline สำคัญอย่างรุนแรง แล้วย่อกลับมารีเทสโซนเดิมเพื่อเดินทางต่อตามทิศทางที่เบรก
            * **News Trade (เทรดข่าว):** การวางแผนเทรดตามความผันผวนของตัวเลขเศรษฐกิจสำคัญ เช่น NFP, CPI, PPI หรือการประกาศดอกเบี้ย FOMC
            """)
            
        with guide_col2:
            st.markdown("### ⏰ ความหมายของ Session (ช่วงเวลาการเทรด)")
            st.markdown("""
            * **Asian Session (06:00 - 13:00 น. เวลาไทย):** ตลาดโตเกียว/ออสเตรเลีย ปริมาณซื้อขายต่ำ กราฟมักวิ่งแคบๆ ในกรอบ **Sideway** เหมาะกับการสะสมของหรือเล่นสั้น
            * **London Session (14:00 - 22:00 น. เวลาไทย):** ตลาดยุโรป/ลอนดอนเปิด ปริมาณเงินเริ่มเข้า มักเกิดการสวิงหลอก (**Judas Swing**) เพื่อสร้างเทรนด์จริงของวัน
            * **New York Session (19:30 - 03:00 น. เวลาไทย):** ตลาดอเมริกาเปิด **ผันผวนสูงที่สุด!** ข่าวสำคัญออกเยอะ กราฟทองคำมักวิ่งแรงและไกลที่สุดในวันช่วงนี้
            * **Overlap Session (19:30 - 22:00 น. เวลาไทย):** ช่วงลอนดอนและนิวยอร์กเปิดซ้อนพร้อมกัน มีสภาพคล่องสูงสุดในรอบ 24 ชั่วโมง กราฟเคลื่อนที่ได้คมและแรงที่สุด
            """)

# ==========================================
# TAB 2: TRADE HISTORY, EDIT, DELETE & BACKUP
# ==========================================
with tab2:
    st.header("📜 ประวัติออเดอร์และการจัดการข้อมูล")
    
    if not st.session_state.trades:
        st.info("ยังไม่มีประวัติออเดอร์ที่บันทึกไว้")
    else:
        df = pd.DataFrame(st.session_state.trades)
        display_df = df.drop(columns=["image_data"], errors="ignore")
        
        exp_col1, exp_col2 = st.columns(2)
        with exp_col1:
            csv_data = display_df.to_csv(index=False).encode('utf-8-sig')
            st.download_button("📥 ดาวน์โหลด CSV", data=csv_data, file_name="trade_history.csv", mime="text/csv", use_container_width=True)
        with exp_col2:
            json_data = json.dumps(st.session_state.trades, ensure_ascii=False, indent=4)
            st.download_button("💾 สำรองข้อมูล JSON (Backup)", data=json_data, file_name="trade_backup.json", mime="application/json", use_container_width=True)
            
        st.dataframe(display_df, use_container_width=True)
        
        st.divider()
        st.subheader("⚙️ แก้ไข / ลบ / ดูรูปภาพกราฟ")
        
        trade_ids = [t["id"] for t in st.session_state.trades]
        selected_id = st.selectbox("เลือก ID ออเดอร์", trade_ids)
        
        selected_index = next(i for i, t in enumerate(st.session_state.trades) if t["id"] == selected_id)
        current_trade = st.session_state.trades[selected_index]
        
        # ถอดรหัสแสดงผลรูปภาพอย่างปลอดภัย
        if current_trade.get("image_data"):
            try:
                img_str = current_trade["image_data"]
                if img_str.startswith("data:image"):
                    base64_data = img_str.split(",")[1]
                    img_bytes = base64.b64decode(base64_data)
                    st.image(img_bytes, caption=f"🖼️ รูปภาพกราฟออเดอร์ #{selected_id}", use_container_width=True)
                else:
                    st.image(img_str, caption=f"🖼️ รูปภาพกราฟออเดอร์ #{selected_id}", use_container_width=True)
            except Exception as e:
                st.error(f"ไม่สามารถแสดงรูปภาพได้: {e}")
            
        edit_c1, edit_c2, edit_c3 = st.columns(3)
        with edit_c1:
            new_sl = st.number_input("ปรับราคา SL", value=float(current_trade["sl"]), format="%.3f")
            new_tp = st.number_input("ปรับราคา TP", value=float(current_trade["tp"]), format="%.3f")
        with edit_c2:
            status_list = ["Active (ถืออยู่)", "TP Hit (ชนะ)", "SL Hit (แพ้)", "Closed Manual (ปิดมือ)"]
            cur_status = current_trade.get("status", "Active (ถืออยู่)")
            idx = status_list.index(cur_status) if cur_status in status_list else 0
            new_status = st.selectbox("สถานะ", status_list, index=idx)
            
            def_pnl = current_trade["max_profit"] if new_status == "TP Hit (ชนะ)" else (-current_trade["max_loss"] if new_status == "SL Hit (แพ้)" else current_trade.get("pnl", 0.0))
            actual_pnl = st.number_input("กำไร/ขาดทุน จริง ($)", value=float(def_pnl), format="%.2f")
        with edit_c3:
            new_note = st.text_area("โน้ต", value=current_trade.get("note", ""))
            
            b_col1, b_col2 = st.columns(2)
            with b_col1:
                if st.button("🔄 อัปเดต", type="primary", use_container_width=True):
                    st.session_state.trades[selected_index].update({
                        "sl": new_sl, "tp": new_tp, "status": new_status, "pnl": actual_pnl, "note": new_note
                    })
                    save_data(st.session_state.trades)
                    st.success("อัปเดตเรียบร้อย!")
                    st.rerun()
            with b_col2:
                if st.button("🗑️ ลบออเดอร์", use_container_width=True):
                    st.session_state.trades.pop(selected_index)
                    save_data(st.session_state.trades)
                    st.warning("ลบเรียบร้อย!")
                    st.rerun()

    st.divider()
    st.subheader("📥 นำเข้าข้อมูลสำรอง (Restore Backup)")
    uploaded_file = st.file_uploader("อัปโหลดไฟล์ backup.json เพื่อคืนค่าข้อมูล", type=["json"])
    if uploaded_file is not None:
        try:
            imported_trades = json.load(uploaded_file)
            if st.button("🔄 ยืนยันการคืนค่าข้อมูล"):
                st.session_state.trades = imported_trades
                save_data(imported_trades)
                st.success("คืนค่าข้อมูลสำเร็จ!")
                st.rerun()
        except Exception as e:
            st.error(f"ไฟล์ไม่ถูกต้อง: {e}")

# ==========================================
# TAB 3: PORTFOLIO SUMMARY & EQUITY CURVE
# ==========================================
with tab3:
    st.header("📊 สรุปผลการเทรด & กราฟวิเคราะห์ประสิทธิภาพ")
    
    if st.session_state.trades:
        df_all = pd.DataFrame(st.session_state.trades)
        closed_df = df_all[df_all["status"] != "Active (ถืออยู่)"].copy()
        
        if not closed_df.empty:
            closed_df["cumulative_pnl"] = closed_df["pnl"].cumsum()
            fig_equity = px.line(closed_df, x="timestamp", y="cumulative_pnl", title="📈 กราฟการเติบโตของพอร์ตสะสม (Equity Curve)", markers=True)
            fig_equity.update_traces(line_color="#00FF7F", line_width=3)
            st.plotly_chart(fig_equity, use_container_width=True)
            
            st.divider()
            
            m1, m2, m3, m4 = st.columns(4)
            tot_pnl = closed_df["pnl"].sum()
            wins = closed_df[closed_df["pnl"] > 0]
            losses = closed_df[closed_df["pnl"] < 0]
            win_rate = (len(wins) / len(closed_df)) * 100
            
            g_profit = wins["pnl"].sum()
            g_loss = abs(losses["pnl"].sum())
            pf = (g_profit / g_loss) if g_loss > 0 else g_profit
            
            m1.metric("กำไร/ขาดทุน รวม", f"${tot_pnl:.2f}")
            m2.metric("Win Rate", f"{win_rate:.1f}%")
            m3.metric("Profit Factor", f"{pf:.2f}")
            m4.metric("จำนวนไม้ที่ปิดแล้ว", len(closed_df))
            
            st.divider()
            
            c_chart1, c_chart2 = st.columns(2)
            with c_chart1:
                setup_pnl = closed_df.groupby("setup")["pnl"].sum().reset_index()
                fig_setup = px.bar(setup_pnl, x="setup", y="pnl", title="📊 กำไร/ขาดทุน แยกตาม Setup", color="pnl", color_continuous_scale="RdYlGn")
                st.plotly_chart(fig_setup, use_container_width=True)
                
            with c_chart2:
                session_pnl = closed_df.groupby("session")["pnl"].sum().reset_index()
                fig_session = px.bar(session_pnl, x="session", y="pnl", title="🌍 กำไร/ขาดทุน แยกตาม Session", color="pnl", color_continuous_scale="Viridis")
                st.plotly_chart(fig_session, use_container_width=True)
                
            st.divider()
            fig_mindset = px.pie(closed_df, names="mindset", title="🧠 สัดส่วนสภาพจิตใจและวินัยตอนเข้าเทรด")
            st.plotly_chart(fig_mindset, use_container_width=True)
            
        else:
            st.info("ยังไม่มีออเดอร์ที่ปิดสถานะ (กรุณาอัปเดตสถานะออเดอร์เป็น TP/SL/ปิดมือ ก่อนดูการวิเคราะห์)")
    else:
        st.info("ยังไม่มีข้อมูลสำหรับวิเคราะห์")
