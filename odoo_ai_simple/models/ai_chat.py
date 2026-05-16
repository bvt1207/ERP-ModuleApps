from odoo import models, fields, api
from odoo.exceptions import UserError
import requests
import json
import pytz
from datetime import datetime, timedelta, date

class AIChat(models.Model):
    _name = 'ai.chat'
    _description = 'Trợ lý AI Quản trị (Admin Assistant)'
    _order = 'create_date desc'

    name = fields.Char(string="Tóm tắt", compute="_compute_name", store=True)
    question = fields.Text(string="Câu hỏi", required=True)
    answer = fields.Html(string="Câu trả lời", readonly=True)
    state = fields.Selection([
        ('draft', 'Mới'),
        ('done', 'Đã trả lời')
    ], string="Trạng thái", default='draft')

    @api.depends('question')
    def _compute_name(self):
        for record in self:
            record.name = (record.question[:50] + "...") if record.question else "Hỏi AI..."

    # --- [CẬP NHẬT] HÀM PHỤ TRỢ: TẠO SẢN PHẨM AN TOÀN + NHẬP KHO ---
    def create_products_from_ai(self, product_list):
        """
        Hàm này giúp AI tạo sản phẩm và nhập số lượng tồn kho.
        Tự động xử lý lỗi 'Wrong value for type' nếu chưa cài module Stock.
        Input: [{'name': 'Iphone', 'price': 20000000, 'qty': 10}, ...]
        """
        # 1. Tìm kho mặc định (nếu có)
        location = self.env.ref('stock.stock_location_stock', raise_if_not_found=False)
        if not location:
            # Tìm kho nội bộ đầu tiên làm dự phòng
            location = self.env['stock.location'].search([('usage', '=', 'internal')], limit=1)

        created_records = self.env['product.product']

        for item in product_list:
            # Chuẩn bị dữ liệu
            vals = {
                'name': item.get('name'),
                'list_price': item.get('price', 0),
                'type': 'product', # Mặc định thử tạo Lưu kho
            }
            
            # 2. Thử tạo sản phẩm với cơ chế SAVEPOINT (An toàn)
            try:
                # Tạo điểm lưu tạm thời
                with self.env.cr.savepoint():
                    product = self.env['product.product'].create(vals)
            except Exception:
                # Nếu lỗi, nó tự động quay lại savepoint (không xóa các sp trước)
                # Thử lại với loại 'consu'
                vals['type'] = 'consu'
                product = self.env['product.product'].create(vals)
            
            if product:
                created_records += product

            # 3. Nhập kho (Chỉ chạy nếu tìm thấy Kho và có số lượng > 0)
            qty = item.get('qty', 0)
            if qty > 0 and location:
                try:
                    # Kiểm tra xem có model stock.quant không trước khi gọi
                    if hasattr(self.env, 'stock.quant'):
                        self.env['stock.quant'].create({
                            'product_id': product.id,
                            'location_id': location.id,
                            'inventory_quantity': qty,
                        }).action_apply_inventory()
                except Exception:
                    pass # Bỏ qua lỗi nhập kho nếu hệ thống chưa sẵn sàng
        
        return created_records

    def action_ask_ai(self):
        """
        Gửi câu hỏi lên Gemini và xử lý phản hồi
        """
        for record in self:
            if not record.question:
                continue

            # 1. CẤU HÌNH API
            GEMINI_API_KEY = self.env['ir.config_parameter'].sudo().get_param('gemini.api.key')
            if not GEMINI_API_KEY:
                GEMINI_API_KEY = "AIzaSyC3FwVPXc4165fMK1eMdWesz4aXLUx-38U" # <-- Key của bạn

            MODEL = "models/gemini-2.5-flash" 
            url = f"https://generativelanguage.googleapis.com/v1beta/{MODEL}:generateContent?key={GEMINI_API_KEY}"

            # 2. SYSTEM PROMPT (ĐÃ SỬA ĐỂ TRÁNH LỖI HIỂN THỊ)
            system_prompt = """
            Bạn là Trợ lý ảo AI của hệ thống ERP Odoo (Admin).
            
            1. QUY TẮC TRẢ LỜI (TUÂN THỦ TUYỆT ĐỐI):
               - Nếu cần thực hiện hành động: Chỉ trả về duy nhất chuỗi: `EXECUTE_ORM: <câu lệnh python>`
               - Câu lệnh phải là MỘT BIỂU THỨC DUY NHẤT chạy được trong hàm `eval()`.
               - ❌ CẤM dùng từ khóa `import`.
               - ❌ CẤM dùng dấu chấm phẩy `;`.
               - ❌ CẤM dùng `.mapped()`, `.name` ở cuối lệnh search. HÃY TRẢ VỀ RECORDSET.
               - Luôn bắt đầu bằng `self`.

            2. HƯỚNG DẪN TẠO SẢN PHẨM (CÓ SỐ LƯỢNG):
               - Khi người dùng muốn tạo sản phẩm, hãy trích xuất thông tin thành danh sách.
               - GỌI HÀM: `self.create_products_from_ai([{'name': 'Ten SP', 'price': 10000, 'qty': 50}, ...])`
               - Trong đó: 'price' là giá bán, 'qty' là số lượng tồn kho.
            
            3. HƯỚNG DẪN TẠO KHÁCH HÀNG (PARTNER):
               - Dùng lệnh: `self.env['res.partner'].create({'name': 'Ten Khach', 'email': 'email@example.com', 'phone': '090...'})`
            
            4. HƯỚNG DẪN TẠO EMAIL (CHỈ LƯU NHÁP - KHÔNG GỬI):
               - Khi người dùng muốn gửi email, bạn chỉ được phép TẠO bản ghi trong `mail.mail`.
               - ❌ TUYỆT ĐỐI KHÔNG dùng lệnh `.send()` hay `.send_mail()`.
               - Chỉ dùng lệnh `.create()`.
               - Cú pháp chuẩn: 
                 `self.env['mail.mail'].create({'subject': 'Tiêu đề', 'body_html': '<p>Nội dung...</p>', 'email_to': 'email@example.com'})`

            5. LƯU Ý VỀ THỜI GIAN (BẮT BUỘC DÙNG ODOO):
               - Đầu ngày hôm nay (0h00): `datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)`
               - Hôm qua: `datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=1)`
               - ❌ TUYỆT ĐỐI KHÔNG dùng `fields.Datetime.today()` (vì nó lấy giờ hiện tại).


            6. CẤU TRÚC DATABASE (Models):
               - Email: `mail.mail` (subject, body_html, email_to, email_from, state).
               - Nhân sự: `hr.employee` (name, work_email).
               - Chấm công: `hr.attendance` (employee_id, check_in, check_out).
               - Khách hàng: `res.partner` (name, email, phone).
               - Đơn hàng: `sale.order` (name, amount_total, state).
               - Sản phẩm: `product.product` (name, list_price, qty_available).
            """

            full_content = f"{system_prompt}\n\nUSER QUESTION: {record.question}"

            payload = {
                "contents": [{"parts": [{"text": full_content}]}]
            }
            headers = {'Content-Type': 'application/json'}

            try:
                # 3. GỌI API GEMINI
                response = requests.post(url, headers=headers, data=json.dumps(payload))
                data = response.json()

                if "candidates" in data and data["candidates"]:
                    ai_text = data["candidates"][0]["content"]["parts"][0]["text"]
                    
                    # 4. XỬ LÝ LỆNH TỪ AI
                    if "EXECUTE_ORM:" in ai_text:
                        try:
                            code_part = ai_text.split("EXECUTE_ORM:")[1].strip()
                            code_to_run = code_part.replace('`', '').replace('python', '').replace('datetime.timedelta', 'timedelta').strip()
                            
                            # Môi trường thực thi
                            eval_context = {
                                'self': self,
                                'datetime': datetime,
                                'date': date,
                                'timedelta': timedelta,
                                'pytz': pytz,
                                'fields': fields,
                                'request': self.env
                            }
                            
                            # Chạy lệnh (Lúc này nó sẽ trả về Object Email vừa tạo)
                            result = eval(code_to_run, eval_context)
                            
                            output_html = f"<div class='alert alert-success' style='background-color:#d4edda; color:#155724; padding:10px; border-radius:5px;'>✅ <b>AI thực thi lệnh:</b><br/><code>{code_to_run}</code></div>"

                            # A. Xử lý kết quả trả về (RecordSet)
                            if hasattr(result, '_name'):
                                if not result:
                                    output_html += "<p><i>(Không tìm thấy dữ liệu)</i></p>"
                                else:
                                    count = len(result)
                                    # Hiển thị tiêu đề
                                    if result._name == 'mail.mail':
                                         output_html += f"<p><b>📧 Đã soạn thảo {count} Email (Vui lòng vào Technical kiểm tra):</b></p>"
                                    elif result._name == 'product.product':
                                         output_html += f"<p>🚀 <b>Đã tạo thành công {count} sản phẩm:</b></p>"
                                    else:
                                         output_html += f"<p><b>📊 Tìm thấy {count} kết quả:</b></p>"

                                    output_html += "<ul style='list-style-type: none; padding-left: 0;'>"
                                    
                                    for item in result[:20]: 
                                        # --- FORMAT HIỂN THỊ ---
                                        
                                        # 1. Trường hợp EMAIL (mail.mail)
                                        if item._name == 'mail.mail':
                                             info = f"""
                                             📧 <b>Email ID: {item.id}</b><br/>
                                             - Gửi tới: {item.email_to}<br/>
                                             - Tiêu đề: {item.subject}<br/>
                                             - Trạng thái: <b>{item.state}</b> (Chờ gửi)
                                             """
                                        
                                        # 2. Trường hợp CHẤM CÔNG (ĐÃ FIX LỖI & FORMAT ĐẸP)
                                        elif item._name == 'hr.attendance':
                                            emp_name = item.employee_id.name
                                            
                                            # Xử lý Timezone: Odoo lưu UTC (Naive) -> Convert sang VN
                                            check_in_vn = item.check_in # fallback
                                            if item.check_in:
                                                check_in_utc = pytz.utc.localize(item.check_in)
                                                check_in_vn = check_in_utc.astimezone(pytz.timezone('Asia/Ho_Chi_Minh'))
                                                str_checkin = check_in_vn.strftime('%H:%M %d/%m')
                                            else:
                                                str_checkin = ""

                                            status = "<span style='color:green'>🟢 Đang làm</span>"
                                            
                                            if item.check_out:
                                                check_out_utc = pytz.utc.localize(item.check_out)
                                                check_out_vn = check_out_utc.astimezone(pytz.timezone('Asia/Ho_Chi_Minh'))
                                                str_checkout = check_out_vn.strftime('%H:%M')
                                                status = f"<span style='color:red'>🔴 Về lúc {str_checkout}</span>"
                                            
                                            # Format hiển thị 2 dòng
                                            info = f"""
                                            <b>👤 {emp_name}</b> - {status}<br/>
                                            <span style='color: #666; font-size: 0.9em; padding-left: 15px;'>
                                                🕒 Check-in: {str_checkin}
                                            </span>
                                            """
                                        
                                        # 3. Trường hợp ĐƠN HÀNG
                                        elif item._name == 'sale.order':
                                             info = f"🛒 <b>{item.name}</b> - {item.amount_total:,.0f}đ ({item.state})"
                                        
                                        # 4. [MỚI] Trường hợp SẢN PHẨM (Hiện tồn kho)
                                        elif item._name == 'product.product':
                                             # Kiểm tra xem field qty_available có tồn tại không trước khi gọi để tránh lỗi
                                             qty = item.qty_available if 'qty_available' in item else 0
                                             info = f"📦 <b>{item.name}</b> - Giá: {item.list_price:,.0f}đ - <b>Kho: {qty}</b>"

                                        # 5. Trường hợp khác
                                        else:
                                             info = f"🔹 <b>{item.display_name}</b>"

                                        output_html += f"<li style='border-bottom:1px dashed #ccc; padding:5px;'>{info}</li>"
                                    
                                    output_html += "</ul>"

                            # B. Kết quả dạng khác
                            else:
                                output_html += f"<br/><b>Kết quả:</b> {str(result)}"

                            record.answer = output_html
                            record.state = 'done'
                            
                        except Exception as run_error:
                            record.answer = f"<div style='color:red'>❌ <b>Lỗi thực thi:</b> {str(run_error)}<br/>Code: {code_to_run}</div>"
                    
                    else:
                        record.answer = ai_text.replace('\n', '<br/>')
                        record.state = 'done'
                else:
                    record.answer = "AI không phản hồi."

            except Exception as e:
                record.answer = f"<b style='color:red'>Lỗi hệ thống:</b> {str(e)}"