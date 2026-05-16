<!-- Banner -->
<p align="center">
  <a href="https://www.uit.edu.vn/" title="Trường Đại học Công nghệ Thông tin" style="border: none;">
    <img src="https://i.imgur.com/WmMnSRt.png" alt="Trường Đại học Công nghệ Thông tin | University of Information Technology">
  </a>
</p>

<h1 align="center"><b>Hoạch định nguồn lực doanh nghiệp</b></h>

## THÀNH VIÊN NHÓM

| STT |   MSSV   |              Họ và Tên |                  Email |
| --- | :------: | ---------------------: | ---------------------: |
| 1   | 23521410 |          Bùi Văn Thạch | 23521410@gm.uit.edu.vn |
| 2   | 23520527 |        Nguyễn Bá Hoàng | 23520527@gm.uit.edu.vn |
| 3   | 23520697 | Nguyễn Quốc Nhật Khang | 23520697@gm.uit.edu.vn |
| 4   | 23521393 |           Trần Hữu Tâm | 23521393@gm.uit.edu.vn |

## GIỚI THIỆU MÔN HỌC

- **Tên môn học:** Hoạch định nguồn lực doanh nghiệp
- **Mã môn học:** IS336
- **Mã lớp:** IS336.Q11
- **Năm học:** HK1 (2025 - 2026)
- **Giảng viên**: ThS.Văn Đức Sơn Hà

## GIỚI THIỆU ĐỒ ÁN

Đồ án cuối kỳ môn Hoạch định nguồn lực doanh nghiệp - IS336.Q11 - thầy Văn Đức Sơn Hà

# 🏢 Odoo Advanced ERP Modules - Vận Hành Thông Minh & Tự Động Hóa

[![Platform](https://img.shields.io/badge/Platform-Odoo%20v16%2F17-purple)](https://www.odoo.com/)
[![Focus](https://img.shields.io/badge/Focus-Automation%20%26%20AI%20Integration-blue)](#)
[![Role](https://img.shields.io/badge/Role-Product%20Owner%20%2F%20System%20Architect-orange)](#)

## 📌 Tổng quan dự án

Bộ giải pháp này bao gồm 3 module mở rộng (Custom Addons) được thiết kế trên nền tảng **Odoo ERP**, nhằm tối ưu hóa hiệu suất làm việc của nhân sự, tự động hóa kênh phân phối đại lý và nâng cao trải nghiệm chăm sóc khách hàng đa kênh.

Thay vì chỉ sử dụng các tính năng cơ bản, dự án tập trung vào **kiến trúc tích hợp hệ thống (System Integration)** để biến Odoo thành trung tâm xử lý dữ liệu tự động.

---

## 🏗 Kiến trúc hệ thống & Luồng tích hợp (System Architecture)

Hệ thống được thiết kế theo mô hình Hub-and-Spoke với Odoo đóng vai trò là "Single Source of Truth" (Nguồn dữ liệu gốc duy nhất).

```text
       [ Google Sheets API ]  🌐 (Đại lý đặt hàng)
                 │
                 ▼
 ┌──────────────────────────────┐       ┌────────────────────────┐
 │       Odoo ERP Core          │ ────> │  OpenAI / LLM API      │
 │  (PostgreSQL Database)       │ <──── │  (Trợ lý AI nhân viên) │
 └──────────────────────────────┘       └────────────────────────┘
                 ▲
                 │ (Webhook / Polling)
       [ Telegram Bot API ]   📱 (Khách hàng & Tra cứu đơn)
```

## 📂 Cấu trúc dự án

```text
ERP-ModuleApps/
├── odoo_ai_simple/       # Module AI (Xử lý LLM API & Giao diện trợ lý)
├── odoo_sheet_sync/      # Module Sync (Xử lý Google API & Logic Map data)
├── odoo_telegram_bot/    # Module Bot (Xử lý Long-polling/Webhook & Bot Telegram)
└── README.md
```
