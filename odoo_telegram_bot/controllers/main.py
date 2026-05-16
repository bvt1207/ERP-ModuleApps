from odoo import http
from odoo.http import request, Response
import requests
import json
import logging

_logger = logging.getLogger(__name__)

# --- CẤU HÌNH ---
# ⚠️ DÁN LẠI TOKEN CỦA BẠN VÀO ĐÂY
TELEGRAM_TOKEN = "8557840460:AAH0ghSyjFLu84cWMQqHOE_s8FcpRaGHmBo" 
TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"

class TelegramController(http.Controller):

    @http.route('/telegram/webhook', type='http', auth='public', csrf=False, methods=['POST'])
    def telegram_webhook(self, **kwargs):
        try:
            data = request.get_json_data()
            
            # _logger.info(f"📩 TELEGRAM DATA: {data}") # Bật dòng này nếu muốn debug

            if data and 'message' in data:
                chat_id = data['message']['chat']['id']
                # Lấy username telegram để lưu vào CRM (nếu có)
                username = data['message']['from'].get('username', 'Ẩn danh')
                text = data['message'].get('text', '').strip()
                
                # Xử lý logic và nhận câu trả lời
                reply_text = self._handle_message(text, username)
                
                # Gửi phản hồi
                self._send_telegram_message(chat_id, reply_text)
            
            return Response("OK", status=200)
            
        except Exception as e:
            error_msg = f"❌ LỖI CONTROLLER: {str(e)}"
            print(error_msg)
            return Response("ERROR", status=500)

    def _handle_message(self, text, username):
        # 1. Chào hỏi
        if text.lower() in ['/start', 'hi', 'xin chào', 'hello']:
            return (
                "🤖 Chào bạn đến với Odoo Shop Bot!\n\n"
                "📌 **Tra cứu đơn hàng:** Nhập mã đơn (VD: S00072)\n"
                "📞 **Đăng ký tư vấn:** Nhập theo cú pháp:\n"
                "`Tư vấn: Tên, SĐT, Nhu cầu`\n"
                "(VD: Tư vấn: Anh Thạch, 0909123456, Mua máy tính)"
            )

        # 2. Xử lý TẠO LEAD (Cú pháp: "Tư vấn: ...")
        if text.lower().startswith('tư vấn:') or text.lower().startswith('lead:'):
            try:
                # Cắt chuỗi: "Tư vấn: Tên, SĐT, Nhu cầu"
                content = text.split(':', 1)[1].strip() # Lấy phần sau dấu hai chấm
                parts = content.split(',') # Tách bằng dấu phẩy
                
                # Kiểm tra xem khách nhập đủ thông tin không
                if len(parts) < 2:
                    return "⚠️ Thiếu thông tin! Vui lòng nhập: Tư vấn: Tên, SĐT, Nhu cầu"

                contact_name = parts[0].strip()
                phone = parts[1].strip()
                # Nếu có phần thứ 3 là ghi chú, nếu không thì để trống
                note = parts[2].strip() if len(parts) > 2 else "Khách quan tâm chung"

                # --- TẠO LEAD TRONG ODOO ---
                lead_vals = {
                    'name': f"[Telegram] {contact_name} cần tư vấn",
                    'contact_name': contact_name,
                    'phone': phone,
                    'description': f"Nhu cầu: {note}\nTelegram User: @{username}",
                    'type': 'lead', # Hoặc 'opportunity'
                    'user_id': False, # Để trống để vào pool chung, hoặc gán ID sale cụ thể
                }
                # Dùng sudo() để tạo lead mà không cần login
                new_lead = request.env['crm.lead'].sudo().create(lead_vals)
                
                return f"✅ Đã ghi nhận thông tin!\nCảm ơn {contact_name}. Nhân viên sẽ gọi lại cho bạn qua số {phone} sớm nhất.\nMã hồ sơ: {new_lead.id}"

            except Exception as e:
                print(f"Lỗi tạo Lead: {e}")
                return "❌ Có lỗi xảy ra khi lưu thông tin. Vui lòng thử lại sau."

        # 3. Xử lý TRA CỨU ĐƠN HÀNG (Logic cũ)
        search_key = text.strip()
        # Tìm gần đúng mã đơn hàng
        order = request.env['sale.order'].sudo().search([('name', 'ilike', search_key)], limit=1)
            
        if order:
            status_map = {'draft': 'Nháp', 'sent': 'Đã gửi', 'sale': 'Đã xác nhận', 'done': 'Hoàn tất', 'cancel': 'Đã hủy'}
            status = status_map.get(order.state, order.state)
            total = "{:,.0f}".format(order.amount_total)
            return f"📦 Đơn {order.name} | {order.partner_id.name}\n📊 Trạng thái: {status}\n💰 Tổng: {total} {order.currency_id.symbol}"
        
        # 4. Mặc định
        return "⚠️ Tôi không hiểu. Vui lòng nhập Mã đơn hàng hoặc cú pháp 'Tư vấn: Tên, SĐT...'"

    def _send_telegram_message(self, chat_id, text):
        payload = {'chat_id': chat_id, 'text': text} # Bỏ parse_mode markdown để tránh lỗi ký tự
        try:
            requests.post(TELEGRAM_API_URL, json=payload)
        except Exception as e:
            print(f"❌ LỖI GỬI TELEGRAM: {e}")

    # Link moi lan chay :https://api.telegram.org/bot<TOKEN_CỦA_BẠN>/setWebhook?url=<LINK_NGROK_CỦA_BẠN>/telegram/webhook