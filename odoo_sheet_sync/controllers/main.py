from odoo import http
from odoo.http import request, Response
import json
import logging

_logger = logging.getLogger(__name__)

class GoogleSheetController(http.Controller):

    @http.route('/api/sheet/order', type='http', auth='public', csrf=False, methods=['POST'])
    def create_order_from_sheet(self, **kwargs):
        try:
            data = request.get_json_data()
            _logger.info(f"DATA TỪ SHEET: {data}") 

            khach_hang = data.get('ten_khach')
            so_dien_thoai = data.get('sdt')
            ma_san_pham = data.get('ma_sp')
            
            # --- XỬ LÝ SỐ LƯỢNG AN TOÀN ---
            raw_qty = data.get('so_luong')
            try:
                if raw_qty and str(raw_qty).strip():
                    so_luong = float(raw_qty)
                else:
                    so_luong = 1.0
            except ValueError:
                so_luong = 1.0
            # -------------------------------

            # Tìm/Tạo Khách
            Partner = request.env['res.partner'].sudo()
            partner = Partner.search([('phone', '=', so_dien_thoai)], limit=1)
            if not partner:
                partner = Partner.create({'name': khach_hang, 'phone': so_dien_thoai})

            # Tìm Sản phẩm
            Product = request.env['product.product'].sudo()
            product = Product.search([('default_code', '=', ma_san_pham)], limit=1)
            
            if not product:
                return Response(json.dumps({'status': 'error', 'msg': f'Không tìm thấy SP mã {ma_san_pham}'}), status=200)

            # Tạo Đơn
            SaleOrder = request.env['sale.order'].sudo()
            order = SaleOrder.create({
                'partner_id': partner.id,
                'state': 'draft',
                'order_line': [(0, 0, {
                    'product_id': product.id,
                    'product_uom_qty': so_luong,
                    'price_unit': product.list_price,
                })]
            })

            return Response(json.dumps({
                'status': 'success',
                'order_name': order.name,
                'amount': order.amount_total
            }), status=200, headers={'Content-Type': 'application/json'})

        except Exception as e:
            return Response(json.dumps({'status': 'error', 'msg': str(e)}), status=500)