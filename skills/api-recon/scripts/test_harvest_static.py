#!/usr/bin/env python3
"""Regression guard for harvest_static.extract_endpoints.

Covers the query-string extraction fix: endpoints whose string literal carries
an inline `?a=...` query were silently dropped because `?` broke the closing-quote
anchor. Run: python3 test_harvest_static.py
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from harvest_static import extract_endpoints  # noqa: E402

# (js snippet, expected endpoint present, expected query param present-or-None)
CASES = [
    ('api.get("/api/users/profile?userId=" + id)', "/api/users/profile", "userId"),
    ("url: '/rest/orders/list?page='+p", "/rest/orders/list", "page"),
    ('fetch(`/api/search?q=` + term)', "/api/search", "q"),
    ("window.open('/service/report/export?from='+a+'&to='+b)",
     "/service/report/export", "from"),
    ('xhr.open("GET", "/gateway/v1/items?category=" + c)', "/gateway/v1/items", "category"),
    ("var u = '/backend/metrics?scope='+s", "/backend/metrics", "scope"),
    # control: no-query path must still extract (no regression)
    ('api.get("/api/catalog/categories/list")', "/api/catalog/categories/list", None),
    # control: .js asset must stay filtered out
    ('<script src="/static/app/main.bundle.js">', None, None),
]


def main():
    failures = []
    for js, want_ep, want_qp in CASES:
        api, other, qparams = extract_endpoints(js)
        found = api | other
        qp_paths = {q.split("\t", 1)[0] for q in qparams}
        qp_names = {q.split("\t", 1)[1] for q in qparams if "\t" in q}
        if want_ep is None:
            if js.endswith('.js">') and found:
                failures.append(f"asset not filtered: {found} <= {js}")
            continue
        if want_ep not in found:
            failures.append(f"missing endpoint {want_ep!r} <= {js}  (got {sorted(found)})")
        if want_qp and (want_ep not in qp_paths or want_qp not in qp_names):
            failures.append(f"missing qparam {want_qp!r} for {want_ep!r} <= {js}  (got {sorted(qparams)})")

    if failures:
        print("FAIL (%d):" % len(failures))
        for f in failures:
            print("  -", f)
        sys.exit(1)
    print("OK: %d cases passed" % len(CASES))


if __name__ == "__main__":
    main()
