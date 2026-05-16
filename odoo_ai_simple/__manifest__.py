{
    'name': 'Simple AI Assistant',
    'version': '1.0',
    'summary': 'Trợ lý AI Quản trị (Admin Assistant)',
    'author': 'Ten_Cua_Ban',
    
    # --- PHẦN QUAN TRỌNG CẦN BỔ SUNG ---
    # stock: Để dùng tính năng Lưu kho, Nhập kho (stock.quant)
    # sale_management: Để dùng tính năng Đơn hàng (sale.order)
    # hr_attendance: Để dùng tính năng Chấm công
    'depends': ['base', 'web', 'hr_attendance', 'stock', 'sale_management'], 
    # -----------------------------------

    'data': [
        'views/ai_chat_view.xml', 
        'security/ir.model.access.csv',
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}