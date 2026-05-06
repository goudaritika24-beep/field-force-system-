export default function AIInsights({ insights }) {
  if (!insights) return null;

  const riskColors = {
    none: 'var(--color-success)',
    low: 'var(--color-info)',
    medium: 'var(--color-warning)',
    high: 'var(--color-danger)'
  };

  const riskLabels = {
    none: '✅ No Risk',
    low: 'ℹ️ Low Risk',
    medium: '⚠️ Medium Risk',
    high: '🚨 High Risk'
  };

  return (
    <div className="ai-insights">
      <div className="ai-insights-header">
        <span className="ai-icon">🤖</span>
        <h3>AI Analysis</h3>
        <span className="ai-badge">Powered by MockAI</span>
      </div>

      <div className="ai-insights-grid">
        <div className="ai-card">
          <div className="ai-card-label">Summary</div>
          <div className="ai-card-content">{insights.ai_summary || insights.summary}</div>
        </div>

        <div className="ai-card">
          <div className="ai-card-label">Risk Assessment</div>
          <div className="ai-card-content">
            <span 
              className="risk-badge" 
              style={{ backgroundColor: riskColors[insights.risk_flag || insights.riskFlag] + '20', color: riskColors[insights.risk_flag || insights.riskFlag] }}
            >
              {riskLabels[insights.risk_flag || insights.riskFlag] || 'Unknown'}
            </span>
          </div>
        </div>

        <div className="ai-card">
          <div className="ai-card-label">Follow-up Recommendation</div>
          <div className="ai-card-content">{insights.follow_up_recommendation || insights.followUpRecommendation}</div>
        </div>

        <div className="ai-card">
          <div className="ai-card-label">Suggested Next Action</div>
          <div className="ai-card-content">{insights.suggested_next_action || insights.suggestedNextAction}</div>
        </div>
      </div>
    </div>
  );
}
