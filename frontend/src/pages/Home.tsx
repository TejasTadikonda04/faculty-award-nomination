import { Link } from "react-router-dom";

export function Home() {
  return (
    <div className="page home">
      <section className="hero card-elevated">
        <p className="eyebrow">Texas A&amp;M · Research awards</p>
        <h1 className="hero-title">Choose how you are using this workspace</h1>
        <p className="lede">
          This prototype skips real sign-in. Pick a role to open the right tools:
          nominees explore awards and test fit from a résumé; nominators run the
          committee view backed by your CV index and LLM ranking.
        </p>
        <div className="role-grid">
          <Link to="/nominee" className="role-card">
            <span className="role-label">I am a</span>
            <span className="role-name">Nominee</span>
            <span className="role-desc">
              Search awards, read details, paste your CV text to see likely
              matches (embedding similarity over extracted award files).
            </span>
            <span className="role-cta">Continue →</span>
          </Link>
          <Link to="/nominator" className="role-card role-card-alt">
            <span className="role-label">I am on the</span>
            <span className="role-name">Awards committee</span>
            <span className="role-desc">
              Describe criteria; retrieve CV excerpts from Pinecone and get a
              ranked short list with model-written reasoning.
            </span>
            <span className="role-cta">Continue →</span>
          </Link>
        </div>
      </section>
    </div>
  );
}
