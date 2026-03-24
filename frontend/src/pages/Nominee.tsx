import { useEffect, useMemo, useState } from "react";
import {
  getAward,
  getHealth,
  listAwards,
  matchResume,
  type AwardSummary,
  type Health,
  type ResumeMatch,
} from "../api/client";

export function Nominee() {
  const [health, setHealth] = useState<Health | null>(null);
  const [query, setQuery] = useState("");
  const [awards, setAwards] = useState<AwardSummary[]>([]);
  const [loadingList, setLoadingList] = useState(true);
  const [listError, setListError] = useState<string | null>(null);

  const [selected, setSelected] = useState<string | null>(null);
  const [detailText, setDetailText] = useState<string | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);

  const [resume, setResume] = useState("");
  const [matches, setMatches] = useState<ResumeMatch[] | null>(null);
  const [matchLoading, setMatchLoading] = useState(false);
  const [matchError, setMatchError] = useState<string | null>(null);

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

  async function runMatch() {
    setMatchError(null);
    setMatches(null);
    setMatchLoading(true);
    try {
      const m = await matchResume(resume, 10);
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
          <p
            className={
              health.config_ok ? "status-pill ok" : "status-pill warn"
            }
          >
            API: {health.config_ok ? "keys present" : health.config_error ?? "check .env"} ·{" "}
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
                className={
                  selected === a.filename ? "award-row active" : "award-row"
                }
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
        <p className="panel-intro">
          Paste CV or biosketch text. The app embeds it with the same model as
          ingestion and ranks extracted award descriptions by cosine similarity
          (fast, local scoring — not the LLM).
        </p>
        <textarea
          className="textarea"
          rows={10}
          value={resume}
          onChange={(e) => setResume(e.target.value)}
          placeholder="Paste your CV text here (at least a few sentences)…"
        />
        <button
          type="button"
          className="btn primary"
          disabled={matchLoading || resume.trim().length < 20}
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
            {matches.map((m) => (
              <li key={m.filename}>
                <div className="match-head">
                  <span className="match-name">{m.filename.replace(".txt", "")}</span>
                  <span className="match-score">
                    {(m.score * 100).toFixed(1)}% similarity
                  </span>
                </div>
                <p className="match-prev">{m.preview}</p>
              </li>
            ))}
          </ol>
        )}
      </section>
    </div>
  );
}
