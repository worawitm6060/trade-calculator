import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime

# ตั้งค่าหน้า Web App
st.set_page_config(
    page_title="XAUUSD Trade Calculator & Journal",
    page_icon="📈",
    layout="wide"
)

# ไฟล์สำหรับบันทึกข้อมูลย้อนหลัง (Data Persistence)
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

# โหลดข้อมูลเข้า Session State
if "trades" not in st.session_state:
    st.session_state.trades = load_data()

st.title("📈 XAUUSD Trade Calculator & Journal")
st.caption("ระบบคำนวณความเสี่ยง และบันทึกประวัติออเดอร์เทรดทองคำ")

# สร้าง Tabs สำหรับแยกหน้าการทำงาน
tab1, tab2, tab3 = st.tabs(["🧮 คำนวณ & บันทึกออเดอร์", "📜 ประวัติ & จัดการออเดอร์", "📊 สรุปภาพรวมพอร์ต"])

# ==========================================
# TAB 1: CALCULATOR & SAVE ORDER
# ==========================================
with tab1:
    st.header("คำนวณแผนการเทรด")
    
    col_input, col_result = st.columns([1, 1])
    
    with col_input:
        capital = st.number_input("ทุนในพอร์ตปัจจุบัน ($)", min_value=1.0, value=100.0, step=10.0)
        symbol = st.selectbox("สินทรัพย์", ["XAUUSD (ทองคำ)", "EURUSD", "GBPUSD", "BTCUSD"])
        side = st.radio("ฝั่งการเทรด", ["BUY", "SELL"], horizontal=True)
        
        # เลือกโหมดขนาด Lot (กรอกเอง หรือ ให้คำนวณจาก % Risk)
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
            
            if side == "BUY":
                sl_price = entry_price - sl_distance
                tp_price = entry_price + (sl_distance * rr_target)
            else:
                sl_price = entry_price + sl_distance
                tp_price = entry_price - (sl_distance * rr_target)
                
            st.info(f"📍 คำนวณอัตโนมัติ -> SL: {sl_price:.3f} | TP: {tp_price:.3f}")

        # คำนวณระยะ SL/TP
        if side == "BUY":
            sl_dist = entry_price - sl_price
            tp_dist = tp_price - entry_price
        else:
            sl_dist = sl_price - entry_price
            tp_dist = entry_price - tp_price

        # กำหนดขนาด Lot
        multiplier = 100.0 if "XAUUSD" in symbol else 100000.0
        if lot_mode == "กรอกขนาด Lot เอง":
            lot = st.number_input("ขนาด Lot Size", min_value=0.01, value=0.01, step=0.01, format="%.2f")
        else:
            risk_percent_input = st.number_input("ยอมเสียได้กี่ % ของพอร์ต", min_value=0.1, max_value=100.0, value=1.0, step=0.5)
            max_risk_usd = (capital * risk_percent_input) / 100.0
            calculated_lot = max_risk_usd / (sl_dist * 100.0) if sl_dist > 0 else 0.01
            lot = max(0.01, round(calculated_lot, 2))
            st.success(f"💡 คำนวณขนาด Lot แนะนำ: **{lot:.2f} Lot** (เสี่ยงไม้นี้ ${max_risk_usd:.2f})")

    max_loss = sl_dist * (lot * 100)
    max_profit = tp_dist * (lot * 100)
    rr_ratio = tp_dist / sl_dist if sl_dist > 0 else 0
    risk_pct = (max_loss / capital) * 100

    with col_result:
        st.subheader("📊 ผลการคำนวณ")
        
        res_c1, res_c2 = st.columns(2)
        res_c1.metric("🔴 ขาดทุนสูงสุด (SL)", f"-${max_loss:.2f}", f"{risk_pct:.1f}% ของพอร์ต", delta_color="inverse")
        res_c2.metric("🟢 กำไรสูงสุด (TP)", f"+${max_profit:.2f}", f"{(max_profit/capital)*100:.1f}% ของพอร์ต")
        
        st.write(f"⚖️ **Risk-to-Reward Ratio (RR):** `1 : {rr_ratio:.2f}`")
        st.write(f"📏 **ระยะ SL:** {sl_dist:.3f} USD ({sl_dist*100:.0f} จุด)")
        st.write(f"🎯 **ระยะ TP:** {tp_dist:.3f} USD ({tp_dist*100:.0f} จุด)")
        
        st.divider()
        note = st.text_input("บันทึกโน้ตเพิ่มเติม (ถ้ามี)", placeholder="เช่น เข้าตามสัญญาณ M5 Rejection")
        
        if st.button("💾 บันทึกออเดอร์นี้ลง Journal", type="primary", use_container_width=True):
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
                "status": "Active (ถืออยู่)",
                "pnl": 0.0,
                "note": note
            }
            st.session_state.trades.append(new_trade)
            save_data(st.session_state.trades)
            st.success("✅ บันทึกออเดอร์เรียบร้อยแล้ว!")
            st.rerun()

# ==========================================
# TAB 2: TRADE HISTORY & EDITING & DELETING
# ==========================================
with tab2:
    st.header("📜 ประวัติออเดอร์และการจัดการ")
    
    if not st.session_state.trades:
        st.info("ยังไม่มีประวัติออเดอร์ที่บันทึกไว้")
    else:
        df = pd.DataFrame(st.session_state.trades)
        
        # ปุ่มดาวน์โหลด CSV
        csv_data = df.to_csv(index=False).encode('utf-8-sig')
        st.download_button(
            label="📥 ดาวน์โหลดประวัติทั้งหมด (CSV)",
            data=csv_data,
            file_name=f"trade_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
        )
        
        st.dataframe(df, use_container_width=True)
        
        st.divider()
        st.subheader("⚙️ แก้ไข / ลบ ออเดอร์")
        
        trade_ids = [t["id"] for t in st.session_state.trades]
        selected_id = st.selectbox("เลือก ID ออเดอร์ที่ต้องการจัดการ", trade_ids)
        
        selected_index = next(i for i, t in enumerate(st.session_state.trades) if t["id"] == selected_id)
        current_trade = st.session_state.trades[selected_index]
        
        edit_c1, edit_c2, edit_c3 = st.columns(3)
        
        with edit_c1:
            new_sl = st.number_input("ปรับราคา SL ใหม่", value=float(current_trade["sl"]), format="%.3f", key="edit_sl")
            new_tp = st.number_input("ปรับราคา TP ใหม่", value=float(current_trade["tp"]), format="%.3f", key="edit_tp")
            
        with edit_c2:
            status_list = ["Active (ถืออยู่)", "TP Hit (ชนะ)", "SL Hit (แพ้)", "Closed Manual (ปิดมือ)"]
            current_status = current_trade.get("status", "Active (ถืออยู่)")
            status_index = status_list.index(current_status) if current_status in status_list else 0
            
            new_status = st.selectbox("สถานะออเดอร์", status_list, index=status_index)
            
            if new_status == "TP Hit (ชนะ)":
                default_pnl = current_trade["max_profit"]
            elif new_status == "SL Hit (แพ้)":
                default_pnl = -current_trade["max_loss"]
            else:
                default_pnl = current_trade.get("pnl", 0.0)
                
            actual_pnl = st.number_input("กำไร/ขาดทุน จริงที่ปิด ($)", value=float(default_pnl), format="%.2f")

        with edit_c3:
            new_note = st.text_area("แก้ไขโน้ต", value=current_trade.get("note", ""))
            
            btn_col1, btn_col2 = st.columns(2)
            with btn_col1:
                if st.button("🔄 อัปเดตข้อมูล", type="primary", use_container_width=True):
                    e_price = current_trade["entry"]
                    l_size = current_trade["lot"]
                    s_side = current_trade["side"]
                    
                    s_dist = (e_price - new_sl) if s_side == "BUY" else (new_sl - e_price)
                    t_dist = (new_tp - e_price) if s_side == "BUY" else (e_price - new_tp)
                    
                    m_loss = round(s_dist * (l_size * 100), 2)
                    m_profit = round(t_dist * (l_size * 100), 2)
                    r_ratio = round(t_dist / s_dist, 2) if s_dist > 0 else 0
                    
                    st.session_state.trades[selected_index].update({
                        "sl": new_sl,
                        "tp": new_tp,
                        "max_loss": m_loss,
                        "max_profit": m_profit,
                        "rr": r_ratio,
                        "status": new_status,
                        "pnl": actual_pnl,
                        "note": new_note
                    })
                    save_data(st.session_state.trades)
                    st.success(f"อัปเดตออเดอร์ #{selected_id} สำเร็จ!")
                    st.rerun()
                    
            with btn_col2:
                if st.button("🗑️ ลบออเดอร์นี้", use_container_width=True):
                    st.session_state.trades.pop(selected_index)
                    save_data(st.session_state.trades)
                    st.warning(f"ลบออเดอร์ #{selected_id} เรียบร้อยแล้ว!")
                    st.rerun()

        st.divider()
        with st.expander("🚨 โซนอันตราย (Danger Zone)"):
            if st.button("🔥 ลบประวัติออเดอร์ทั้งหมด (Clear All)", type="secondary"):
                st.session_state.trades = []
                save_data([])
                st.error("ลบประวัติออเดอร์ทั้งหมดเรียบร้อยแล้ว!")
                st.rerun()

# ==========================================
# TAB 3: PORTFOLIO SUMMARY & ANALYTICS
# ==========================================
with tab3:
    st.header("📊 สรุปผลการเทรดรวม (Performance Analytics)")
    
    if st.session_state.trades:
        df_all = pd.DataFrame(st.session_state.trades)
        closed_trades = df_all[df_all["status"] != "Active (ถืออยู่)"]
        
        sum_c1, sum_c2, sum_c3, sum_c4 = st.columns(4)
        
        total_pnl = closed_trades["pnl"].sum() if not closed_trades.empty else 0.0
        win_trades = closed_trades[closed_trades["pnl"] > 0]
        loss_trades = closed_trades[closed_trades["pnl"] < 0]
        
        total_closed = len(closed_trades)
        win_rate = (len(win_trades) / total_closed * 100) if total_closed > 0 else 0.0
        
        gross_profit = win_trades["pnl"].sum() if not win_trades.empty else 0.0
        gross_loss = abs(loss_trades["pnl"].sum()) if not loss_trades.empty else 0.0
        profit_factor = (gross_profit / gross_loss) if gross_loss > 0 else (gross_profit if gross_profit > 0 else 0.0)
        
        sum_c1.metric("จำนวนออเดอร์ทั้งหมด", len(df_all))
        sum_c2.metric("ออเดอร์ที่ปิดแล้ว", total_closed)
        sum_c3.metric("กำไร/ขาดทุน สะสม", f"${total_pnl:.2f}", delta_color="normal" if total_pnl>=0 else "inverse")
        sum_c4.metric("Win Rate", f"{win_rate:.1f}%")
        
        st.divider()
        st.subheader("📈 สถิติเชิงลึก")
        st_c1, st_c2, st_c3 = st.columns(3)
        
        avg_win = win_trades["pnl"].mean() if not win_trades.empty else 0.0
        avg_loss = abs(loss_trades["pnl"].mean()) if not loss_trades.empty else 0.0
        
        st_c1.metric("Profit Factor", f"{profit_factor:.2f}")
        st_c2.metric("กำไรเฉลี่ยเมื่อชนะ (Avg Win)", f"+${avg_win:.2f}")
        st_c3.metric("ขาดทุนเฉลี่ยเมื่อแพ้ (Avg Loss)", f"-${avg_loss:.2f}")
    else:
        st.info("ยังไม่มีข้อมูลสำหรับสรุปผล")
