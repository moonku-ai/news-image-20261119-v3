"""Tests for news-image-20261119 v3 — broadsheet front page of 19 Nov 2026.

TDD: these tests were written BEFORE main.py. Run with:
    python3 -m unittest discover -s . -p "test_main.py" -v
from ~/workspace/makefun/news-image-20261119-v3/
"""
import hashlib
import os
import struct
import subprocess
import sys
import tempfile
import unittest
import zlib

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)


def run_entry(out_dir):
    """Run main.py the way the grader does and return the output path."""
    env = dict(os.environ)
    env["MAKEFUN_OUTPUT_DIR"] = out_dir
    out = os.path.join(out_dir, "entry.png")
    proc = subprocess.run(
        [sys.executable, os.path.join(HERE, "main.py")],
        env=env, capture_output=True, text=True, timeout=120,
    )
    if proc.returncode != 0:
        raise AssertionError(
            "main.py failed rc=%d\nstdout=%s\nstderr=%s"
            % (proc.returncode, proc.stdout, proc.stderr)
        )
    return out


def read_png(path):
    with open(path, "rb") as fh:
        data = fh.read()
    assert data[:8] == b"\x89PNG\r\n\x1a\n", "bad PNG signature"
    pos = 8
    chunks = []
    idat = b""
    width = height = bit_depth = color_type = None
    while pos < len(data):
        (length,) = struct.unpack(">I", data[pos:pos + 4])
        ctype = data[pos + 4:pos + 8]
        payload = data[pos + 8:pos + 8 + length]
        crc_stored, = struct.unpack(">I", data[pos + 8 + length:pos + 12 + length])
        crc_real = zlib.crc32(ctype + payload) & 0xFFFFFFFF
        assert crc_stored == crc_real, "bad CRC in chunk %r" % ctype
        chunks.append(ctype)
        if ctype == b"IHDR":
            width, height, bit_depth, color_type = struct.unpack(">IIBB", payload[:10])
        elif ctype == b"IDAT":
            idat += payload
        elif ctype == b"IEND":
            break
        pos += 12 + length
    assert chunks[-1] == b"IEND", "no IEND chunk"
    raw = zlib.decompress(idat)
    return data, width, height, bit_depth, color_type, raw


class TestPngEncoder(unittest.TestCase):
    def test_output_is_valid_png_1024(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = run_entry(tmp)
            _, w, h, depth, ctype, raw = read_png(out)
            self.assertEqual((w, h), (1024, 1024))
            self.assertEqual(depth, 8)
            self.assertEqual(ctype, 2)  # truecolour RGB
            # filter byte per row + 3 bytes per pixel
            self.assertEqual(len(raw), 1024 * (1 + 1024 * 3))

    def test_output_under_1mib(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = run_entry(tmp)
            self.assertLessEqual(os.path.getsize(out), 1048576)


class TestDeterminism(unittest.TestCase):
    def test_two_runs_byte_identical(self):
        with tempfile.TemporaryDirectory() as d1, tempfile.TemporaryDirectory() as d2:
            a = run_entry(d1)
            b = run_entry(d2)
            with open(a, "rb") as fh:
                ha = hashlib.sha256(fh.read()).hexdigest()
            with open(b, "rb") as fh:
                hb = hashlib.sha256(fh.read()).hexdigest()
            self.assertEqual(ha, hb)


class TestFontCoverage(unittest.TestCase):
    def test_every_printed_char_has_a_glyph(self):
        import main
        texts = [main.MASTHEAD_TITLE, main.MASTHEAD_DATE]
        for story in main.STORIES:
            texts += [story["kicker"], story["headline"], story["subhead"]]
        missing = set()
        for text in texts:
            for ch in text:
                if ch != " " and ch not in main.FONT:
                    missing.add(ch)
        self.assertEqual(missing, set(), "missing glyphs: %r" % sorted(missing))

    def test_all_glyphs_are_7_rows_of_5(self):
        import main
        for ch, rows in main.FONT.items():
            self.assertEqual(len(rows), 7, "glyph %r not 7 rows" % ch)
            for row in rows:
                self.assertEqual(len(row), 5, "glyph %r row not 5 wide" % ch)
                self.assertTrue(set(row) <= set("#."), "glyph %r bad chars" % ch)


class TestTextWrap(unittest.TestCase):
    def test_wrapped_lines_fit_their_panels(self):
        import main
        for story in main.STORIES:
            for text, scale, max_w in (
                (story["headline"], 3, story["text_w"]),
                (story["subhead"], 2, story["text_w"]),
            ):
                for line in main.wrap_text(text, scale, max_w):
                    self.assertLessEqual(
                        main.text_width(line, scale), max_w,
                        "line %r too wide for panel" % line,
                    )

    def test_masthead_fits(self):
        import main
        self.assertLessEqual(main.text_width(main.MASTHEAD_TITLE, 6), 992)
        self.assertLessEqual(main.text_width(main.MASTHEAD_DATE, 3), 992)


class TestPanelsDrawn(unittest.TestCase):
    def test_each_story_panel_is_not_blank(self):
        """Every story panel region must contain real drawn content
        (colour variance), not a flat fill. Threshold is 6: the hero
        panel is flat-colour by design (blue field, gold stars, white
        text), so it legitimately holds ~7 distinct colours, while a
        truly blank panel holds 1-2."""
        import main
        with tempfile.TemporaryDirectory() as tmp:
            out = run_entry(tmp)
            _, _, _, _, _, raw = read_png(out)
            # raw rows: 1 filter byte + 1024*3 bytes
            stride = 1 + 1024 * 3

            def pixel(x, y):
                off = y * stride + 1 + x * 3
                return raw[off], raw[off + 1], raw[off + 2]

            for story in main.STORIES:
                x0, y0, x1, y1 = story["panel"]
                seen = set()
                for yy in range(y0, y1, 7):
                    for xx in range(x0, x1, 7):
                        seen.add(pixel(xx, yy))
                self.assertGreater(
                    len(seen), 6,
                    "panel %r looks blank/flat (%d colours)"
                    % (story["kicker"], len(seen)),
                )

    def test_date_and_day_appear_in_source_strings(self):
        import main
        self.assertIn("19 NOVEMBER 2026", main.MASTHEAD_DATE)
        self.assertIn("THURSDAY", main.MASTHEAD_DATE)
        self.assertEqual(len(main.STORIES), 6)

    def test_text_blocks_fit_inside_panels(self):
        """Regression: v3 first render clipped the GTA and Voyager
        subheads/headlines past the bottom edge of their 216px panels.
        Every story's kicker + headline + subhead block must end
        inside its panel with margin to spare."""
        import main
        for story in main.STORIES:
            layout = main.story_layout(story)
            x0, y0, x1, y1 = story["panel"]
            self.assertLessEqual(
                layout["text_end_y"], y1 - 8,
                "text of %r overflows panel bottom (%d > %d)"
                % (story["kicker"], layout["text_end_y"], y1 - 8),
            )
            self.assertLessEqual(
                layout["art_bottom_y"], layout["text_top_y"],
                "art of %r overlaps its text" % story["kicker"],
            )


if __name__ == "__main__":
    unittest.main()
