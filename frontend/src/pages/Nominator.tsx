import { useEffect, useMemo, useState } from "react";
import {
  getAward,
  getHealth,
  listAwards,
  rankFaculty,
  type AwardSummary,
  type Health,
  type RankingRow,
} from "../api/client";

export function Nominator() {
  const [health, setHealth] = useState<Health | null>(null);
  const [query, setQuery] = useState("");
  const [awards, setAwards] = useState<AwardSummary[]>([]);
  const [loadingList, setLoadingList] = useState(true);
  const [listError, setListError] = useState<string | null>(null);

  const [selected, setSelected] = useState<string | null>(null);
  const [selectedTitle, setSelectedTitle] = useState<string | null>(null);
  const [awardText, setAwardText] = useState<string | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [rows, setRows] = useState<RankingRow[] | null>(null);
  const [rawResponse, setRawResponse] = useState<string | null>(null);

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

  async function selectAward(award: AwardSummary) {
    setSelected(award.filename);
    setSelectedTitle(award.title);
    setDetailLoading(true);
    setAwardText(null);
    setRows(null);
    setError(null);
    try {
      const { text } = await getAward(award.filename);
      setAwardText(text);
    } catch {
      setAwardText(null);
    } finally {
      setDetailLoading(false);
    }
  }

  async function run() {
    if (!awardText) return;
    setError(null);
    setRows(null);
    setRawResponse(null);
    setLoading(true);
    try {
      const res = await rankFaculty(awardText);
      setRows(res.rankings);
      setRawResponse(res.raw_response);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Request failed");
    } finally {
      setLoading(false);
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
                onClick={() => void selectAward(a)}
              >
                <span className="award-title">{a.title}</span>
                <span className="award-prev">{a.preview}</span>
              </button>
            </li>
          ))}
        </ul>
      </section>

      <section className="panel">
        <h2 className="panel-title">Faculty rankings</h2>
        {!selected && (
          <p className="muted">Select an award on the left to rank faculty.</p>
        )}
        {selected && detailLoading && <p className="muted">Loading award…</p>}
        {selected && !detailLoading && awardText && (
          <>
            <p className="panel-intro">{selectedTitle}</p>
            <button
              type="button"
              className="btn primary"
              disabled={loading}
              onClick={() => void run()}
            >
              {loading ? "Retrieving & ranking…" : "Generate top matches"}
            </button>
            {error && <p className="error">{error}</p>}

            {rows && rows.length > 0 && (
              <div className="rank-block">
                <h3 className="subhead">Ranked faculty</h3>
                <ol className="rank-list">
                  {rows.slice().sort((a, b) => b.match_score - a.match_score).map((r) => (
                    <li key={`${r.rank}-${r.faculty_name}`}>
                      <div className="rank-head">
                        <span className="rank-num">#{r.rank}</span>
                        <span className="rank-name">{r.faculty_name}</span>
                        <span className="rank-score">Score {r.match_score}/10</span>
                      </div>
                      <p className="rank-reason">{r.reasoning}</p>
                    </li>
                  ))}
                </ol>
              </div>
            )}

            {!loading && !error && rawResponse && (!rows || rows.length === 0) && (
              <div className="rank-block">
                <h3 className="subhead">LLM Response</h3>
                <pre className="detail-block">{rawResponse}</pre>
              </div>
            )}

          </>
        )}
      </section>
    </div>
  );
}
