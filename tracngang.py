#!/usr/bin/env python3
"""tracngang.py - ve trac ngang theo ban mau 02.TNTK (ADS Civil), xuat DXF de mo trong OpenCADStudio.

    ~/.claude/skills/trac-doc/.venv/bin/python ~/.claude/skills/ve-trac-ngang/tracngang.py input.json out.dxf

input.json (xem vi-du.json):
{
  "ntd": "SLT_HUNGHOC.ntd",      # file TDN 3.5: POLE + TARGETL/TARGETR
  "ox": 0, "oy": 0,              # goc: tim coc dau tien, chan chu Km cua hang tren
  "B": 10,                       # be rong ghi so lieu moi ben tim (m); duong tu nhien ve them 1 m
  "mss": null,                   # muc so sanh co dinh; null = floor(cao do thap nhat) - 3
  "duong_cu": true,              # ve ket cau duong cu giua 2 diem ma mep 1/2
  "cocs": null,                  # tuy chon: chi ve cac coc co ten trong danh sach
  "thiet_ke": {...} | null,      # tuy chon: duong do trac doc (giong tracdoc.py) -> cao do tim TK
  "mat_duong": {"trai": 3.0, "phai": 3.0, "i": 0.02} | null
                                 # tuy chon: mat duong TK 2 mai doc i tu tim (can thiet_ke)
}
Ty le 1/200 hai chieu: 1 don vi = 1 m (khong phong dai dung). Chu so lieu 0.4, ten coc/ly trinh 0.6.
Trang: 2 cot x 2 hang mat cat (buoc 30 x 25), cac trang cach nhau 130 theo X.
"""
import json
import math
import os
import sys

import ezdxf
from ezdxf.enums import TextEntityAlignment as TA

# ---- layer chuan (ten TK_268_..., mau theo ban mau 02.TNTK) ----
LAYERS = {
    "BANG": ("TK_268_BangTracNgang", 3),          # TK-ADS-9402
    "CHU": ("TK_268_ChuTracNgang", 3),            # TK-ADS-9403
    "DONG": ("TK_268_DuongDongTracNgang", 8),     # TK-ADS-9405
    "LT": ("TK_268_LyTrinhTracNgang", 3),         # TK-ADS-9407
    "DV": ("TK_268_DiaVatTracNgang", 3),          # TK-ADS-9408
    "TN": ("TK_268_TracNgangTuNhien", 3),         # KS-TUY-2501
    "CU": ("TK_268_TracNgangDuongCu", 8),         # KS-TUY-2502
    "CDTIM": ("TK_268_GhiChuCaoDoTim", 2),        # TK-ADS-9453
    "DOC": ("TK_268_GhiChuDoDocTK", 2),           # TK-ADS-9454
    "MD": ("TK_268_MatDuongTracNgang", 1),        # TK-DBO-1703
    "TIMTK": ("TK_268_DuongTKTimTuyen", 1),       # TK-DBO-1601 (dung chung voi trac doc)
}
ST = "TK_268_ChuBang"  # arial.ttf wf 0.8 (thay ADS-Bang trac ngang = ads civil.shx wf 0.8)

H = 0.4          # chu so lieu
HT = 0.6         # ten coc, ly trinh
SP = 0.4         # khoang cach toi thieu giua 2 nhan dung (ban mau 0.4)
# bang (do tu ban mau, so voi mep tren bang T va tim xt)
X_HDR0, X_HDR1, X_END = -18.0, -11.0, 11.0
ROWS = [  # ten, day, dinh (so voi T)
    ("Khoảng cách mia", -7.2, -5.6), ("Cao độ tự nhiên", -5.6, -3.6),
    ("Khoảng cách lẻ thiết kế", -3.6, -2.0), ("Cao độ thiết kế", -2.0, 0.0),
]
DT = -11.65      # mep tren bang so voi chan chu Km
DX_COT, DY_HANG, DX_TRANG = 30.0, 25.0, 130.0

# ---- dia vat theo ma diem trong .ntd (cot 4 cua TARGETL/R) ----
# block goc (chua scale) do lai tu ban mau; chen scale 0.2
BLOCKS = {
    "12": ("TK_268_TuongGach", "Tường gạch"),
    "7": ("TK_268_CotDien", "Cột điện"),
}


def doc_ntd(path):
    secs = []
    for ln in open(path, encoding="utf-8", errors="replace"):
        t = ln.rstrip("\r\n").split("\t")
        if t[0] == "POLE":
            secs.append({"ten": t[1], "s": float(t[2]), "z": float(t[3]), "L": [], "R": []})
        elif t[0] in ("TARGETL", "TARGETR") and secs:
            code = None
            if len(t) > 3 and not t[3].startswith("NOBLOCK"):
                code = ("mep" + t[4]) if (t[3] == "0" and len(t) > 4) else t[3]
            secs[-1][t[0][-1]].append((float(t[1]), float(t[2]), code))
    for c in secs:
        c["pts"] = list(reversed(c["L"])) + [(0.0, c["z"], "tim")] + c["R"]
    return secs


def interp(pts, o):
    for (o1, z1, _), (o2, z2, _) in zip(pts, pts[1:]):
        if o1 <= o <= o2 and o2 > o1:
            return z1 + (z2 - z1) * (o - o1) / (o2 - o1)
    return None


def cat(pts, B):
    """Cat duong tu nhien: tra (pts_ve [-B-1..B+1], pts_ghi [-B..B])."""
    inner = [p for p in pts if -B < p[0] < B]
    ghi = list(inner)
    for o in (-B, B):
        z = interp(pts, o)
        if z is not None:
            if o < 0:
                ghi.insert(0, (o, z, None))
            else:
                ghi.append((o, z, None))
    ve = list(ghi)
    for o in (-B - 1, B + 1):
        z = interp(pts, o)
        if z is not None:
            if o < 0:
                ve.insert(0, (o, z, None))
            else:
                ve.append((o, z, None))
    return ve, ghi


def gian(xs, sp=SP):
    """Gian cac nhan dung cach nhau >= sp, giu tam cum (giong ADS)."""
    grp = [[x] for x in xs]  # moi nhom: danh sach vi tri mong muon
    def pos(g):
        c = sum(g) / len(g)
        return [c + (k - (len(g) - 1) / 2) * sp for k in range(len(g))]
    changed = True
    while changed:
        changed = False
        for i in range(len(grp) - 1):
            if pos(grp[i + 1])[0] - pos(grp[i])[-1] < sp - 1e-9:
                grp[i] += grp.pop(i + 1)
                changed = True
                break
    out = []
    for g in grp:
        out += pos(g)
    return out


def km(s):
    k = int(s // 1000)
    return f"Km {k} + {s - 1000 * k:.2f}"


class TN:
    def __init__(self, cfg):
        self.doc = ezdxf.new("R2018", setup=False)
        self.doc.header["$INSUNITS"] = 6
        self.doc.header["$DWGCODEPAGE"] = "ANSI_1258"
        for n, c in LAYERS.values():
            self.doc.layers.add(n, color=c, linetype="Continuous")
        self.doc.styles.add(ST, font="arial.ttf").dxf.width = 0.8
        self.msp = self.doc.modelspace()
        self.L = {k: v[0] for k, v in LAYERS.items()}
        self.B = cfg.get("B", 10.0)
        self.mss_fix = cfg.get("mss")
        self.duong_cu = cfg.get("duong_cu", True)
        self.md = cfg.get("mat_duong")
        self._blocks()
        self.dv_la = {}

    # --- primitive ---
    def t(self, s, x, y, h, rot, al, lay, color=None):
        a = {"layer": self.L[lay], "style": ST, "height": h, "width": 0.8, "rotation": rot}
        if color is not None:
            a["color"] = color
        self.msp.add_text(s, dxfattribs=a).set_placement((x, y), align=al)

    def ln(self, p, q, lay, color=None):
        a = {"layer": self.L[lay]}
        if color is not None:
            a["color"] = color
        self.msp.add_line(p, q, dxfattribs=a)

    def pl(self, pts, lay, closed=False, color=None):
        a = {"layer": self.L[lay]}
        if color is not None:
            a["color"] = color
        return self.msp.add_lwpolyline(pts, close=closed, dxfattribs=a)

    def _blocks(self):
        dv = self.L["DV"]
        b = self.doc.blocks.new("TK_268_TuongGach")  # ban mau 012.Tuong gach.dwg
        b.add_lwpolyline([(0, 0), (0, 9.3078)], dxfattribs={"layer": dv, "color": 7})
        for s, y in (("TƯỜNG", 14.726), ("GẠCH", 10.3078)):
            b.add_text(s, dxfattribs={"layer": dv, "color": 6, "style": ST, "height": 2.0, "width": 0.8}
                       ).set_placement((0, y), align=TA.MIDDLE)
        b = self.doc.blocks.new("TK_268_CotDien")  # ban mau 007.Cot dien.dwg
        a = {"layer": dv, "color": 6}
        b.add_lwpolyline([(-0.495, 0.024), (-0.184, 26.401), (0.161, 26.401), (0.375, 0.024)], dxfattribs=a)
        b.add_lwpolyline([(-2.669, 23.687), (2.767, 23.687)], dxfattribs=a)
        b.add_lwpolyline([(-1.038, 26.184), (1.136, 26.184)], dxfattribs=a)
        for x0, x1, y0, y1 in ((-2.513, -2.335, 23.684, 24.085), (-1.330, -1.152, 23.684, 24.085),
                               (2.375, 2.553, 23.684, 24.085), (1.192, 1.370, 23.706, 24.107),
                               (-0.906, -0.728, 26.202, 26.603), (0.768, 0.946, 26.202, 26.603)):
            b.add_lwpolyline([(x0, y0), (x0, y1), (x1, y1), (x1, y0)], close=True, dxfattribs=a)
        # dau coc: ten coc + ly trinh (attribute) + co tim; goc = tim, chan chu Km.
        # Hinh co do lai tu anh nguoi dung gui 2026-11-26 (ban mau la proxy ADS, khung 1.47 x 0.70)
        b = self.doc.blocks.new("TK_268_DauCoc")
        a = {"layer": self.L["BANG"]}
        b.add_line((0, -1.55), (0, -1.02), dxfattribs=a)               # que tim phia tren
        for s in (-1, 1):
            b.add_line((-s * 0.13, -1.69), (s * 0.255, -1.32), dxfattribs=a)  # can co (cheo qua tim tao dau x)
            b.add_lwpolyline([(s * 0.255, -1.32), (s * 0.51, -1.06), (s * 0.705, -1.45)], close=True,
                             dxfattribs=a)                             # la co tam giac
        for tag, y, lay, dflt in (("TEN_COC", 0.8, "CHU", "Cọc 1"), ("LY_TRINH", 0.0, "LT", "Km 0 + 0.00")):
            ad = b.add_attdef(tag, (0, y), dflt, dxfattribs={
                "layer": self.L[lay], "style": ST, "height": HT, "width": 0.8, "prompt": tag})
            ad.set_placement((0, y), align=TA.CENTER)

    # --- 1 mat cat ---
    def mat_cat(self, c, xt, yk, ztk=None):
        B = self.B
        T = yk + DT
        ve, ghi = cat(c["pts"], B)
        zs = [p[1] for p in ve] + ([ztk] if ztk is not None else [])
        mss = self.mss_fix if self.mss_fix is not None else math.floor(min(zs)) - 3
        Y = lambda z: T + (z - mss)
        X = lambda o: xt + o
        # tieu de
        # dau coc: block TK_268_DauCoc (ten coc, ly trinh la attribute) + duong tim xuong bang
        ref = self.msp.add_blockref("TK_268_DauCoc", (xt, yk), dxfattribs={"layer": self.L["BANG"]})
        ref.add_auto_attribs({"TEN_COC": f"Cọc {c['ten']}", "LY_TRINH": km(c["s"])})
        self.ln((xt, T), (xt, yk - 1.55), "BANG")
        # bang
        for _, y0, y1 in ROWS:
            self.ln((xt + X_HDR0, T + y0), (xt + X_END, T + y0), "BANG")
        self.ln((xt + X_HDR0, T), (xt + X_END, T), "BANG")
        for x in (X_HDR0, X_HDR1, X_END):
            self.ln((xt + x, T + ROWS[0][1]), (xt + x, T), "BANG")
        for ten, y0, y1 in ROWS:
            self.t(ten, xt + (X_HDR0 + X_HDR1) / 2, T + (y0 + y1) / 2, H, 0, TA.MIDDLE, "BANG")
        self.msp.add_mtext(f"MSS: {mss:g}", dxfattribs={
            "layer": self.L["CHU"], "style": ST, "char_height": H, "attachment_point": 9,
            "insert": (xt + X_HDR1, T + 0.2)})
        # duong tu nhien + dong
        self.pl([(X(o), Y(z)) for o, z, _ in ve], "TN")
        for o, z, _ in ghi:
            self.ln((X(o), Y(z)), (X(o), T), "DONG")
        # hang cao do tu nhien (nhan dung, gian 0.4)
        xs = gian([X(o) for o, _, _ in ghi])
        for x, (o, z, _) in zip(xs, ghi):
            self.t(f"{z:.2f}", x, T - 3.6 - 0.2, H, 90, TA.MIDDLE_RIGHT, "CHU", 3)
        # hang khoang cach mia
        y0m, y1m = T - 7.2, T - 5.6
        for o, _, _ in ghi:
            self.ln((X(o), y0m), (X(o), y1m), "CHU", 3)
        hep = []
        for (o1, _, _), (o2, _, _) in zip(ghi, ghi[1:]):
            d = o2 - o1
            if d >= 1.0:
                self.t(f"{d:.2f}", X((o1 + o2) / 2), T - 6.4, H, 0, TA.MIDDLE, "CHU", 3)
            else:
                hep.append((X((o1 + o2) / 2), d))
        for x, (_, d) in zip(gian([h[0] for h in hep]), hep):
            self.t(f"{d:.2f}", x, T - 6.4, H, 90, TA.MIDDLE, "CHU", 3)
        # dia vat + duong cu
        for o, z, code in ghi:
            if code in BLOCKS:
                self.msp.add_blockref(BLOCKS[code][0], (X(o), Y(z)),
                                      dxfattribs={"layer": self.L["DV"], "xscale": 0.2, "yscale": 0.2})
            elif code and not code.startswith("mep") and code != "tim":
                self.dv_la[code] = self.dv_la.get(code, 0) + 1
                self.t(f"Mã {code}", X(o), Y(z) + 0.5, H, 90, TA.MIDDLE_LEFT, "DV", 6)
        if self.duong_cu:
            m1 = [p for p in c["pts"] if p[2] == "mep1"]
            m2 = [p for p in c["pts"] if p[2] == "mep2"]
            if m1 and m2 and m1[0][0] < 0 < m2[0][0]:
                a, b = m1[0], m2[0]
                mat = [(a[0], a[1]), (0.0, c["z"]), (b[0], b[1])]
                for dz in (0.07, 0.17):
                    self.pl([(X(o), Y(z - dz)) for o, z in mat], "CU")
                vien = [(X(a[0]), Y(a[1]))] + [(X(o), Y(z - 0.29)) for o, z in mat] + [(X(b[0]), Y(b[1]))]
                self.pl(vien, "CU")
                h = self.msp.add_hatch(color=8, dxfattribs={"layer": self.L["CU"]})
                h.set_pattern_fill("ANSI31", color=8, scale=0.02)  # set_pattern_fill mac dinh color=7
                h.paths.add_polyline_path(vien + [(X(o), Y(z)) for o, z in reversed(mat)][1:-1], is_closed=True)
        # thiet ke (tuy chon)
        if ztk is not None:
            yt = Y(ztk)
            self.msp.add_circle((xt, yt), 0.1, dxfattribs={"layer": self.L["TIMTK"]})
            self.pl([(xt, yt), (xt + 1.0, yt + 3.0), (xt + 5.88, yt + 3.0)], "CDTIM")
            self.msp.add_mtext(f"Cao độ thiết kế: {ztk:.2f}", dxfattribs={
                "layer": self.L["CDTIM"], "style": ST, "char_height": H, "attachment_point": 7,
                "insert": (xt + 1.0, yt + 3.2)})
            tk = [(0.0, ztk)]
            if self.md:
                i = self.md.get("i", 0.02)
                tk = [(-self.md["trai"], ztk - i * self.md["trai"]), (0.0, ztk),
                      (self.md["phai"], ztk - i * self.md["phai"])]
                self.pl([(X(o), Y(z)) for o, z in tk], "MD")
                for (o1, z1), (o2, z2) in zip(tk, tk[1:]):
                    ang = math.degrees(math.atan2(z2 - z1, o2 - o1))
                    self.t(f"{100 * i:.2f}%", X((o1 + o2) / 2), Y((z1 + z2) / 2) + 0.19, H, ang,
                           TA.BOTTOM_CENTER, "DOC")
            for o, z in tk:
                self.ln((X(o), Y(z)), (X(o), T), "CDTIM")
                self.t(f"{z:.2f}", X(o), T - 0.2, H, 90, TA.MIDDLE_RIGHT, "CHU", 2)
                self.ln((X(o), T - 3.6), (X(o), T - 2.0), "CHU", 2)
            for (o1, _), (o2, _) in zip(tk, tk[1:]):
                self.t(f"{o2 - o1:.2f}", X((o1 + o2) / 2), T - 2.8, H, 0, TA.MIDDLE, "CHU", 2)


def main():
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    cfg = json.load(open(sys.argv[1], encoding="utf-8"))
    secs = doc_ntd(cfg["ntd"])
    if cfg.get("cocs"):
        secs = [c for c in secs if c["ten"] in cfg["cocs"]]
    ze = None
    if cfg.get("thiet_ke"):
        sys.path.insert(0, os.path.expanduser("~/.claude/skills/trac-doc"))
        import tracdoc
        tk = cfg["thiet_ke"]
        td = tracdoc.TD(0, 0)
        td.tk_thong_so(tk["s0"], tk["z0"], tk["sp"], tk["zp"], tk["s1"], tk["z1"], tk["R"])
        ze = td.ze
    tn = TN(cfg)
    ox, oy = cfg.get("ox", 0.0), cfg.get("oy", 0.0)
    for i, c in enumerate(secs):
        p, j = divmod(i, 4)
        col, row = divmod(j, 2)
        tn.mat_cat(c, ox + p * DX_TRANG + col * DX_COT, oy - row * DY_HANG, ze(c["s"]) if ze else None)
    tn.doc.saveas(sys.argv[2], encoding="utf-8")
    print(f"{len(secs)} mat cat, {math.ceil(len(secs) / 4)} trang, {len(tn.msp)} doi tuong")
    if tn.dv_la:
        print("Ma dia vat chua co ky hieu (ghi chu 'Ma ...'):", tn.dv_la)


if __name__ == "__main__":
    main()
