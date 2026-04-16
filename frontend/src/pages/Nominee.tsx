import { useEffect, useMemo, useState } from "react";
import {
  getAward,
  getCvText,
  getHealth,
  listAwards,
  listCvs,
  matchResume,
  type AwardSummary,
  type Health,
  type ResumeMatch,
} from "../api/client";

function formatCvName(filename: string): string {
  return filename
    .replace(".pdf", "")
    .replace(/-/g, " ")
    .replace(/\b\w/g, (c) => c.toUpperCase());
}

export function Nominee() {
  const [health, setHealth] = useState<Health | null>(null);
  const [query, setQuery] = useState("");
  const [awards, setAwards] = useState<AwardSummary[]>([]);
  const [loadingList, setLoadingList] = useState(true);
  const [listError, setListError] = useState<string | null>(null);

  const [selected, setSelected] = useState<string | null>(null);
  const [detailText, setDetailText] = useState<string | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);

  const [cvFiles, setCvFiles] = useState<string[]>([]);
  const [selectedCv, setSelectedCv] = useState("");
  const [cvLoading, setCvLoading] = useState(false);
  const [cvText, setCvText] = useState("");

  const [matches, setMatches] = useState<ResumeMatch[] | null>(null);
  const [matchLoading, setMatchLoading] = useState(false);
  const [matchError, setMatchError] = useState<string | null>(null);
  const [customRules, setCustomRules] = useState("");

  useEffect(() => {
    getHealth()
      .then(setHealth)
      .catch(() => setHealth(null));
  }, []);

  useEffect(() => {
    setLoadingList(true);
    setListError(null);
    listAwards()
      .then(setAwards)
      .catch((e) => setListError(e instanceof Error ? e.message : "Load failed"))
      .finally(() => setLoadingList(false));
  }, []);

  useEffect(() => {
    listCvs()
      .then(setCvFiles)
      .catch(() => setCvFiles([]));
  }, []);

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return awards;
    return awards.filter(
      (a) =>
        a.filename.toLowerCase().includes(q) ||
        a.title.toLowerCase().includes(q) ||
        a.preview.toLowerCase().includes(q),
    );
  }, [awards, query]);

  async function openAward(filename: string) {
    setSelected(filename);
    setDetailLoading(true);
    setDetailText(null);
    try {
      const { text } = await getAward(filename);
      setDetailText(text);
    } catch {
      setDetailText("Could not load this award.");
    } finally {
      setDetailLoading(false);
    }
  }

  async function handleCvSelect(filename: string) {
    setSelectedCv(filename);
    setCvText("");
    setMatches(null);
    setMatchError(null);
    if (!filename) return;
    setCvLoading(true);
    try {
      const { text } = await getCvText(filename);
      setCvText(text);
    } catch {
      setMatchError("Could not extract text from this CV.");
    } finally {
      setCvLoading(false);
    }
  }

  async function runMatch() {
    setMatchError(null);
    setMatches(null);
    setMatchLoading(true);
    try {
      const m = await matchResume(cvText, 10, customRules || undefined);
      setMatches(m);
    } catch (e) {
      setMatchError(e instanceof Error ? e.message : "Match failed");
    } finally {
      setMatchLoading(false);
    }
  }

  return (
    <div className="page two-col">
      <section className="panel">
        <h2 className="panel-title">Award catalog</h2>
        {health && (
          <p className={health.config_ok ? "status-pill ok" : "status-pill warn"}>
            API: {health.config_ok ? "keys present" : (health.config_error ?? "check .env")} ·{" "}
            {health.awards_extracted_count} award file(s) on disk
          </p>
        )}
        <input
          type="search"
          className="input"
          placeholder="Search awards…"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          aria-label="Search awards"
        />
        {loadingList && <p className="muted">Loading awards…</p>}
        {listError && <p className="error">{listError}</p>}
        <ul className="award-list">
          {filtered.map((a) => (
            <li key={a.filename}>
              <button
                type="button"
                className={selected === a.filename ? "award-row active" : "award-row"}
                onClick={() => void openAward(a.filename)}
              >
                <span className="award-title">{a.title}</span>
                <span className="award-prev">{a.preview}</span>
              </button>
            </li>
          ))}
        </ul>
      </section>

      <section className="panel">
        <h2 className="panel-title">Award detail</h2>
        {!selected && (
          <p className="muted">Select an award on the left to read the full text.</p>
        )}
        {selected && detailLoading && <p className="muted">Loading…</p>}
        {selected && !detailLoading && detailText && (
          <pre className="detail-block">{detailText}</pre>
        )}

        <hr className="divider" />

        <h3 className="subhead">Résumé match preview</h3>
        <label className="label" htmlFor="cv-select">Select a faculty CV</label>
        <select
          id="cv-select"
          className="input"
          value={selectedCv}
          onChange={(e) => void handleCvSelect(e.target.value)}
        >
          <option value="">— choose a CV —</option>
          {cvFiles.map((f) => (
            <option key={f} value={f}>
              {formatCvName(f)}
            </option>
          ))}
        </select>
        {cvLoading && <p className="muted">Loading CV…</p>}
        <details className="custom-rules-details">
          <summary className="custom-rules-summary">Custom rules <span className="custom-rules-hint">(optional — appended to the LLM prompt)</span></summary>
          <textarea
            className="textarea"
            placeholder="e.g. Prefer awards that relate to teaching. Exclude awards requiring doctoral students."
            value={customRules}
            onChange={(e) => setCustomRules(e.target.value)}
            rows={4}
          />
        </details>
        <button
          type="button"
          className="btn primary"
          disabled={matchLoading || cvLoading || cvText.length < 20}
          onClick={() => void runMatch()}
        >
          {matchLoading ? "Scoring…" : "Find likely award matches"}
        </button>
        {matchError && <p className="error">{matchError}</p>}
        {matches && matches.length === 0 && (
          <p className="muted">No award files found to compare against.</p>
        )}
        {matches && matches.length > 0 && (
          <ol className="match-list">
            {matches
              .slice()
              .sort((a, b) => {
                const sa = a.match_score ?? a.score * 10;
                const sb = b.match_score ?? b.score * 10;
                return sb - sa;
              })
              .map((m) => {
              const displayName = m.filename
                .replace(/\.txt$/i, "")
                .replace(/_/g, " ")
                .replace(/-/g, " ")
                .replace(/^[\d.]+\s+/, "")
                .replace(/\s+[\d.]+$/, "")
                .replace(/\b\w/g, (c) => c.toUpperCase())
                .trim();
              return (
                <li key={m.filename}>
                  <div className="match-head">
                    <span className="match-name">{displayName}</span>
                    <span className="match-score">
                      Score {m.match_score ?? (m.score * 10).toFixed(1)}/10
                    </span>
                  </div>
                  <p className="match-prev">{m.reasoning || m.preview}</p>
                </li>
              );
            })}
          </ol>
        )}
      </section>
    </div>
  );
}
