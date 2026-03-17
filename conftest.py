"""
Pytest hooks para reporte HTML (pytest-html) y Allure Report:
título, metadatos, dashboard, screenshots en fallo.
"""

from __future__ import annotations

import html
import time

import allure
import pytest

from utils.config import BASE_URL


def pytest_html_report_title(report) -> None:
    report.title = "Academy E2E — Test Report"


@pytest.hookimpl(trylast=True)
def pytest_configure(config: pytest.Config) -> None:
    """Extra rows in Environment (pytest-metadata)."""
    if not config.getoption("htmlpath", default=None):
        return
    try:
        from pytest_metadata.plugin import metadata_key

        if metadata_key not in config.stash:
            return
        meta = config.stash[metadata_key]
        meta["Project"] = "Academy E2E Automation"
        meta["Target app"] = "SauceDemo"
        meta["BASE_URL"] = BASE_URL
        meta["Stack"] = "Python · pytest · Playwright · POM"
    except Exception:
        pass


def pytest_html_results_summary(prefix, summary, postfix, session) -> None:
    """Dashboard cards + banner above the default summary."""
    tr = session.config.pluginmanager.get_plugin("terminalreporter")
    passed = failed = skipped = errors = 0
    if tr and hasattr(tr, "stats"):
        passed = len(tr.stats.get("passed", []))
        failed = len(tr.stats.get("failed", []))
        skipped = len(tr.stats.get("skipped", []))
        errors = len(tr.stats.get("error", []))
    total = passed + failed + skipped + errors
    duration = getattr(session, "_sessionduration", None)
    if duration is None:
        duration = time.time() - getattr(session, "_starttime", time.time())
    dur_s = f"{duration:.1f}s"

    banner = (
        '<div class="academy-banner">'
        "<strong>Academy E2E</strong> — Reporte generado para capacitación en automatización. "
        "Los tests fallidos incluyen <strong>captura de pantalla</strong> en la fila (Links / extras). "
        f"URL bajo prueba: <code>{html.escape(BASE_URL)}</code>"
        "</div>"
    )
    dash = f"""
    <div class="academy-dashboard">
      <div class="academy-card academy-card--total">
        <div class="academy-card__value">{total}</div>
        <div class="academy-card__label">Total</div>
      </div>
      <div class="academy-card academy-card--pass">
        <div class="academy-card__value">{passed}</div>
        <div class="academy-card__label">Passed</div>
      </div>
      <div class="academy-card academy-card--fail">
        <div class="academy-card__value">{failed + errors}</div>
        <div class="academy-card__label">Failed / Error</div>
      </div>
      <div class="academy-card academy-card--skip">
        <div class="academy-card__value">{skipped}</div>
        <div class="academy-card__label">Skipped</div>
      </div>
      <div class="academy-card">
        <div class="academy-card__value">{html.escape(dur_s)}</div>
        <div class="academy-card__label">Duration</div>
      </div>
    </div>
    """
    prefix.insert(0, banner + dash)


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item: pytest.Item, call: pytest.CallInfo):
    """Adjunta screenshot en pytest-html Y en Allure cuando un test con `page` falla."""
    outcome = yield
    rep = outcome.get_result()
    if rep.when != "call" or not rep.failed:
        return
    page = item.funcargs.get("page")
    if page is None:
        return
    try:
        png_bytes = page.screenshot(full_page=False)
    except Exception:
        return

    # --- Adjuntar en Allure Report ---
    allure.attach(
        png_bytes,
        name="Screenshot on failure",
        attachment_type=allure.attachment_type.PNG,
    )

    # --- Adjuntar en pytest-html ---
    try:
        import pytest_html.extras as html_extras
        extra = html_extras.png(png_bytes, "Screenshot on failure")
        rep.extra = getattr(rep, "extra", []) + [extra]
    except ImportError:
        pass


def pytest_sessionstart(session: pytest.Session) -> None:
    session._starttime = time.time()


def pytest_sessionfinish(session: pytest.Session, exitstatus: int) -> None:
    session._sessionduration = time.time() - getattr(session, "_starttime", time.time())
