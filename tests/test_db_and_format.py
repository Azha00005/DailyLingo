import os

import bot
import db


def setup_module():
    if os.path.exists(db.DB_PATH):
        os.remove(db.DB_PATH)
    db.init()


def teardown_module():
    if os.path.exists(db.DB_PATH):
        os.remove(db.DB_PATH)


def test_items_and_errors():
    item_id = db.add_item(url="https://e.com/a", title="T", category="art", kind="article", junk="x")
    db.update_item(item_id, summary="S", junk="y")
    assert db.get_item(item_id)["summary"] == "S"
    assert "https://e.com/a" in db.seen_urls()
    db.add_errors(item_id, [{"original": "he go", "corrected": "he goes", "explanation": ""}])
    assert db.errors_since(7)[0]["corrected"] == "he goes"


def test_output_is_escaped():
    cards = [{"term": "<b>x</b>", "translation": "a|b", "example": "<script>"}]
    assert "<script>" not in bot.words_list(cards)
    block = bot.quizlet_block(cards)
    assert "&lt;b&gt;x&lt;/b&gt;|a/b" in block


def test_keyboard_skips_non_http_links():
    kb = bot.item_keyboard({"id": 1, "url": "javascript:alert(1)"})
    assert all(btn.url is None for row in kb.inline_keyboard for btn in row)
