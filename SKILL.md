---
name: ve-trac-ngang
description: Vẽ trắc ngang tuyến đường (mặt cắt ngang tự nhiên từ file .ntd TDN 3.5, bảng 4 hàng, ký hiệu địa vật tường gạch/cột điện, kết cấu đường cũ, tùy chọn cao độ + mặt đường thiết kế) theo bản mẫu 02.TNTK.dwg, layer TK_268_..., chữ font unicode (arial.ttf), xuất DXF rồi mở/lưu DWG bằng OpenCADStudio. Dùng khi người dùng yêu cầu vẽ, chỉnh hoặc kiểm tra trắc ngang.
---

# Skill vẽ trắc ngang (theo bản mẫu `02.TNTK.dwg`)

Nguồn: đọc phần trắc ngang của `~/Downloads/Test GT/02.TNTK.dwg` ngày 2026-11-26 (vẽ bằng ADS Civil, 39 mặt cắt tuyến SLT_HUNGHOC). Bản mẫu có nhiều đối tượng proxy ADS (ký hiệu tim, mũi tên độ dốc, điểm đo) nên một số chi tiết là vẽ gần đúng, ghi rõ ở mục 6.

**Cài đặt (một lần):** `git clone https://github.com/Tuanmetal32/TK_268_Ve_trac_ngang ~/.claude/skills/ve-trac-ngang`; cần skill `trac-doc` (repo Tuanmetal32/TK_268_trac_doc) đã cài kèm venv (`~/.claude/skills/trac-doc/.venv`, có ezdxf theo `requirements.txt`).

Máy Linux này không có AutoCAD → dùng script Python + OpenCADStudio (MCP `opencadstudio`). Dùng chung venv của skill `trac-doc` (`~/.claude/skills/trac-doc/.venv`, có ezdxf). Tùy chọn `thiet_ke` gọi `tracdoc.py` của skill `trac-doc` để lấy cao độ tim thiết kế.



## Quy tắc số liệu (người dùng yêu cầu 2026-11-26) — BẮT BUỘC
- Luôn lấy số liệu từ file `.ntd` người dùng gửi (cọc, lý trình, cao độ tự nhiên, điểm trắc ngang TARGETL/TARGETR, mã địa vật, góc/đường cong). Không tự bịa, không suy đoán, không làm tròn hay "làm đẹp" số liệu.
- Số liệu không có trong `.ntd` (đường đỏ/cao độ thiết kế, đáy rãnh, bề rộng và độ dốc mặt đường, kết cấu...) chỉ dùng khi người dùng đưa ra trong cuộc trò chuyện. Thiếu thì DỪNG và hỏi, không tự đặt giá trị giả định.
- Khi báo kết quả: nêu rõ file `.ntd` đã dùng và nguồn của từng số liệu không đến từ `.ntd`.

## Quy tắc lưu file trắc dọc - trắc ngang (người dùng yêu cầu 2026-11-26)
- Trắc dọc và trắc ngang của cùng một tuyến nằm CHUNG một bản vẽ, tên file `TK TDTN.dwg` (kèm `TK TDTN.dxf` trung gian), trong thư mục tuyến `~/Documents/Claude/<thư mục tuyến>/` (ví dụ `~/Documents/Claude/trac_doc_HUNGHOC/TK TDTN.dwg`).
- Trắc dọc đặt ở gốc (ox=0, oy=0); trắc ngang đặt bên dưới: `ox = 18` (mép trái bảng trắc ngang thẳng mép trái bảng trắc dọc), `oy = −80` (cách đáy trắc dọc ≈ 30). Lưu `input.json` (trắc dọc) và `input_tracngang.json` (trắc ngang) trong thư mục tuyến.
- Cách gộp: chạy `tracdoc.py input.json td.dxf` và `ve-trac-ngang/tracngang.py input_tracngang.json tn.dxf` ra scratchpad, rồi gộp bằng ezdxf `Importer(tn, td).import_modelspace(); finalize()` (mang theo layer, style, block) → `TK TDTN.dxf` → OCS `ocs_save_verified` → `TK TDTN.dwg` (2018).
- Sửa trắc dọc hay trắc ngang thì dựng lại cả file `TK TDTN` theo cách trên, không tạo file riêng lẻ. Không đẩy skill lên GitHub khi người dùng chưa yêu cầu.

## 1. Quy trình
1. Xác nhận với người dùng: file `.ntd`, có vẽ phần thiết kế không (cao độ tim từ trắc dọc + bề rộng/độ dốc mặt đường), vị trí đặt `(ox, oy)`.
2. Viết `input.json` (mẫu `vi-du.json`):
   - `ntd` (bắt buộc), `ox, oy` (tim cọc đầu, chân chữ Km hàng trên), `B` = 10 (ghi số liệu ±B, đường tự nhiên vẽ tới ±(B+1)),
   - `mss` (null = floor(cao độ thấp nhất) − 3, bản mẫu đều là −3), `duong_cu` (true),
   - `cocs` (lọc tên cọc), `thiet_ke` (giống `tracdoc.py`), `mat_duong` {trai, phai, i}.
3. `~/.claude/skills/trac-doc/.venv/bin/python ~/.claude/skills/ve-trac-ngang/tracngang.py input.json out.dxf`
4. OCS: `ocs_open` DXF → `ocs_capture` (view `region`, `max_dimension` ≤ 1000; kết quả JSON rất dài, chụp ít) → `ocs_save_verified` ra `.dwg` 2018 (`overwrite: true` nếu ghi đè).
   Lưu ý OCS: mở lại một đường dẫn đang mở sẽ chỉ kích hoạt bản cũ → `ocs_execute {op: close, document_id, discard: true}` trước rồi mới `ocs_open`.
5. Báo người dùng: file, số mặt cắt/trang, mã địa vật chưa có ký hiệu (script in ra), các giả định.

## 2. Bố cục (1 đơn vị = 1 m, tỷ lệ 1/200 cả hai chiều, không phóng đại đứng)
- Trang: 2 cột × 2 hàng mặt cắt; bước cột 30, bước hàng 25, các trang cách nhau 130 theo X. Thứ tự: cột trái trên → dưới, rồi cột phải.
- Gốc mỗi mặt cắt: `xt` = tim, `yk` = chân chữ Km. Mép trên bảng `T = yk − 11.65`. Cao độ z vẽ tại `Y = T + (z − MSS)`.
- Đầu cọc: block `TK_268_DauCoc` (gốc = tim, chân chữ Km), chèn trên layer `TK_268_BangTracNgang`. Gồm 2 attribute `TEN_COC` (`Cọc 1`, y = +0.8, layer `TK_268_ChuTracNgang`) và `LY_TRINH` (`Km 0 + 0.00`, y = 0, layer `TK_268_LyTrinhTracNgang`), TEXT cao 0.6 căn giữa-chân; ký hiệu cờ tim vẽ theo ảnh người dùng gửi 2026-11-26: que tim (0,−1.55)→(0,−1.02); hai cán cờ chéo (∓0.13,−1.69)→(±0.255,−1.32) cắt nhau tạo dấu x tại (0,−1.55); hai lá cờ tam giác (±0.255,−1.32), (±0.51,−1.06), (±0.705,−1.45). Đường tim từ mép trên bảng lên yk − 1.55 (nằm ngoài block). Bản mẫu còn chữ `Cao độ :1.45` đè chữ Km → bỏ.
- Bảng: x từ xt−18 đến xt+11, cột tiêu đề xt−18…xt−11 (rộng 7). 4 hàng tính từ dưới lên (so với T):

| Hàng | Dưới → trên | Nội dung |
|---|---|---|
| Khoảng cách mia | −7.2 → −5.6 | vạch đứng tại mỗi điểm; khoảng cách ≥ 1.0 ghi ngang giữa đoạn, < 1.0 ghi đứng (xoay 90°) |
| Cao độ tự nhiên | −5.6 → −3.6 | TEXT xoay 90°, căn phải-giữa, chân cách mép trên hàng 0.2 |
| Khoảng cách lẻ thiết kế | −3.6 → −2.0 | màu 2, chỉ khi có thiết kế |
| Cao độ thiết kế | −2.0 → 0 | màu 2, chỉ khi có thiết kế |

- Nhãn đứng sát nhau được giãn cách tối thiểu 0.4, giữ tâm cụm (đúng cách ADS làm). Hai điểm cùng khoảng cách (thành rãnh, tường) vẫn ghi cả hai cao độ và khoảng cách 0.00.
- `MSS: −3`: MTEXT cao 0.4, góc phải-dưới tại (xt − 11, T + 0.2).
- Điểm ghi số liệu: điểm đo trong ±B + điểm nội suy tại ±B. Đường tự nhiên thêm điểm nội suy tại ±(B+1).
- Đường dóng: từ mỗi điểm ghi số liệu xuống mép trên bảng.

## 3. Layer (đổi tên từ bản mẫu sang `TK_268_...`, màu giữ nguyên)

| Layer mới | Bản mẫu | Màu | Dùng cho |
|---|---|---|---|
| `TK_268_BangTracNgang` | TK-ADS-9402 | 3 | khung bảng, chữ tiêu đề hàng, đường tim, ký hiệu tim |
| `TK_268_ChuTracNgang` | TK-ADS-9403 | 3 | tên cọc, số liệu bảng (màu đè 3 tự nhiên, 2 thiết kế), vạch hàng mia, MSS |
| `TK_268_DuongDongTracNgang` | TK-ADS-9405 | 8 | đường dóng tự nhiên |
| `TK_268_LyTrinhTracNgang` | TK-ADS-9407 | 3 | chữ `Km 0 + …` |
| `TK_268_DiaVatTracNgang` | TK-ADS-9408 | 3 | ký hiệu địa vật (block) |
| `TK_268_TracNgangTuNhien` | KS-TUY-2501 | 3 | đường tự nhiên (LWPOLYLINE) |
| `TK_268_TracNgangDuongCu` | KS-TUY-2502 | 8 | kết cấu đường cũ + hatch ANSI31 |
| `TK_268_GhiChuCaoDoTim` | TK-ADS-9453 | 2 | đường dóng thiết kế, que + chữ `Cao độ thiết kế: …` |
| `TK_268_GhiChuDoDocTK` | TK-ADS-9454 | 2 | chữ độ dốc `2.00%` trên mặt đường |
| `TK_268_MatDuongTracNgang` | TK-DBO-1703 | 1 | mặt đường thiết kế |
| `TK_268_DuongTKTimTuyen` | TK-DBO-1601 | 1 | vòng tròn r 0.1 tại tim thiết kế (dùng chung với trắc dọc) |

Các layer khác của bản mẫu (TK-DBO-17xx/18xx kết cấu, lề, vỉa hè, taluy; Tmldaoke diện tích) chưa dùng vì chưa có số liệu thiết kế mặt cắt; khi cần thì đổi tên theo cùng quy tắc và hỏi người dùng.

## 4. Chữ (quy đổi sang unicode)
- Bản mẫu: `ADS-Bảng trắc ngang`, `ADS-Bảng biểu`, `ADS-Ghi chú` = `ads civil.shx` wf 0.8; `DIEP`/`ARIALH` = `VnArialH.TTF` (mã TCVN3, ví dụ `Tr¾c ngang tuyÕn`).
- Quy đổi: tất cả dùng style `TK_268_ChuBang` = `arial.ttf` wf 0.8 (cùng style với trắc dọc). Chữ nhập vào luôn là Unicode; chữ lấy từ bản vẽ TCVN3 phải chuyển mã trước khi dùng.
- Cỡ chữ: số liệu và tiêu đề hàng 0.4 (2 mm ở 1/200), tên cọc và lý trình 0.6, chữ trong block địa vật 2.0 × scale 0.2 = 0.4.

## 5. Địa vật (mã điểm trong .ntd)
Dòng `TARGETL/R`: `offset  cao_độ  [mã]`. `0 1` / `0 2` = mép đường trái / phải (dùng vẽ đường cũ); `NOBLOCK*0*` = điểm thường; số khác = mã địa vật, chèn block tại điểm đó, scale 0.2, layer `TK_268_DiaVatTracNgang`:
- `12` → block `TK_268_TuongGach` (bản mẫu `012.Tuong gach.dwg`): que đứng cao 1.86 (màu 7) + chữ `TƯỜNG` / `GẠCH` màu 6 (tím), căn giữa.
- `7` → block `TK_268_CotDien` (bản mẫu `007.Cot dien.dwg`): cột + xà + sứ, màu 6, cao 5.28.
- Mã khác: ghi chữ `Mã <n>` màu 6 xoay 90° trên điểm; script in danh sách để hỏi người dùng ký hiệu.
- Đường cũ (giữa mép 1 và 2): mặt = điểm mép trái, tim, mép phải; 2 đường lớp ở −0.07, −0.17; viền đáy −0.29; hatch ANSI31 scale 0.02 (bản mẫu scale 1.0 theo đơn vị khác), màu 8 gán cứng trên hatch (người dùng yêu cầu 2026-11-26).

## 6. Chưa làm / gần đúng (báo người dùng)
- Ký hiệu tim ở đỉnh, mũi tên độ dốc, điểm đo: bản mẫu là proxy ADS → vẽ gần đúng hoặc bỏ.
- Phần thiết kế chỉ có mặt đường 2 mái từ tim (`mat_duong`); chưa có lề, rãnh, taluy, kết cấu áo đường, siêu cao.
- Bảng diện tích (`S Đào đất c3 nền đường`, `S cpđD loại II`… ở góc trái trên mỗi mặt cắt, chữ đỏ là giá trị m²) chưa vẽ vì cần mặt cắt thiết kế.
- Khung tên A3 (`268 A3-cd xref`) và tiêu đề trang `Trắc ngang tuyến` chưa chèn.
- Đã chạy thử 2026-11-26 với `SLT_HUNGHOC.ntd`: 39 mặt cắt, 10 trang, 2611 đối tượng, 19 tường gạch + 1 cột điện, audit DWG không lỗi.
