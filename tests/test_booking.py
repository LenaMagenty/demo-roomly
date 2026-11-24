from datetime import date, timedelta

import allure
import pytest
from playwright.sync_api import Page, expect

# BUG-01: прошедшее время для текущего дня не отклоняется
XFAIL_REASON = "BUG-01: прошедшее время для сегодняшней даты принимается (script.js не проверяет его)"


def _tomorrow() -> str:
    return (date.today() + timedelta(days=1)).isoformat()


def test_successful_booking(page: Page, base_url: str):
    """Позитивный: корректная бронь показывает подтверждение с деталями."""
    with allure.step("Открыть страницу бронирования"):
        page.goto(base_url, wait_until="domcontentloaded")

    with allure.step("Заполнить форму валидными данными (Средняя, завтра, 10:00-11:30, 6)"):
        page.locator("#room").select_option("medium")
        page.locator("#date").fill(_tomorrow())
        page.locator("#start-time").fill("10:00")
        page.locator("#end-time").fill("11:30")
        page.locator("#participants").fill("6")
        page.locator("#name").fill("Иван Петров")
        page.locator("#email").fill("ivan.petrov@company.ru")

    with allure.step("Нажать «Забронировать»"):
        page.get_by_role("button", name="Забронировать").click()

    with allure.step("Проверить сообщение об успехе и отсутствие ошибок"):
        status = page.locator("#form-status")
        expect(status).to_contain_text("Бронирование создано.")
        expect(status).to_contain_text("Средняя")
        expect(status).to_contain_text(_tomorrow())
        expect(status).to_contain_text("10:00–11:30")
        expect(status).to_contain_text("Иван Петров")
        expect(page.locator(".field.has-error")).to_have_count(0)


def test_invalid_booking(page: Page, base_url: str):
    """Негативный: участников больше вместимости комнаты."""
    with allure.step("Открыть страницу бронирования"):
        page.goto(base_url, wait_until="domcontentloaded")

    with allure.step("Заполнить форму: Малая (до 4), 10 участников"):
        page.locator("#room").select_option("small")
        page.locator("#date").fill(_tomorrow())
        page.locator("#start-time").fill("10:00")
        page.locator("#end-time").fill("11:30")
        page.locator("#participants").fill("10")
        page.locator("#name").fill("Иван Петров")
        page.locator("#email").fill("ivan.petrov@company.ru")

    with allure.step("Нажать «Забронировать»"):
        page.get_by_role("button", name="Забронировать").click()

    with allure.step("Проверить ошибку вместимости и что бронь не создана"):
        expect(page.locator('[data-error-for="participants"]')).to_have_text(
            "В комнате максимум 4 участника."
        )
        expect(page.locator("#form-status")).to_contain_text(
            "Проверьте, пожалуйста, заполнение формы."
        )
        expect(page.locator("#form-status")).not_to_contain_text("Бронирование создано")


@pytest.mark.xfail(strict=True, reason=XFAIL_REASON, raises=AssertionError)
def test_discovered_defect(page: Page, base_url: str):
    """Дефект BUG-01: прошедшее время сегодня должно отклоняться, но принимается."""
    with allure.step("Открыть страницу бронирования"):
        page.goto(base_url, wait_until="domcontentloaded")

    with allure.step("Заполнить форму: сегодня, прошедший интервал 00:30-01:00"):
        page.locator("#room").select_option("medium")
        page.locator("#date").fill(date.today().isoformat())
        page.locator("#start-time").fill("00:30")
        page.locator("#end-time").fill("01:00")
        page.locator("#participants").fill("6")
        page.locator("#name").fill("Иван Петров")
        page.locator("#email").fill("ivan.petrov@company.ru")

    with allure.step("Нажать «Забронировать», фактически получим успех вместо ошибки"):
        page.get_by_role("button", name="Забронировать").click()

    with allure.step("Проверить, что прошедший интервал отклонён (упадёт, это BUG-01)"):
        expect(page.locator("#form-status")).not_to_contain_text("Бронирование создано")
