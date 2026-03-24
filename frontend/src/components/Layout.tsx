import type { ReactNode } from "react";
import { Link, useLocation } from "react-router-dom";

export function Layout({ children }: { children: ReactNode }) {
  const loc = useLocation();
  const onHome = loc.pathname === "/";

  return (
    <div className="shell">
      <header className="topbar">
        <Link to="/" className="brand">
          <span className="brand-mark" aria-hidden />
          <span className="brand-text">
            <span className="brand-title">Research Awards</span>
            <span className="brand-sub">Faculty nomination workspace</span>
          </span>
        </Link>
        {!onHome && (
          <nav className="nav-mini" aria-label="Primary">
            <Link to="/nominee" className="nav-link">
              Nominee
            </Link>
            <Link to="/nominator" className="nav-link">
              Nominator
            </Link>
            <Link to="/" className="nav-link muted">
              Exit
            </Link>
          </nav>
        )}
      </header>
      <main className="main">{children}</main>
      <footer className="footer">
        <p>
          Texas A&amp;M–styled demo UI · Matching uses your backend RAG pipeline
          (Pinecone CVs + TAMU AI).
        </p>
      </footer>
    </div>
  );
}
