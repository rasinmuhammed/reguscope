'use client'
import React, { useState } from 'react';
import { Search, FileText, AlertCircle, Clock, CheckCircle, Loader2, ExternalLink, Calendar, MapPin, Hash, TrendingUp, Info } from 'lucide-react';

// ==========================================
// TYPE DEFINITIONS
// ==========================================

interface Citation {
  document_id: string;
  section_number: string;
  effective_date: string;
  jurisdiction: string;
  relevance_score: number;
  snippet: string;
}

interface QueryResult {
  answer: string;
  citations: Record<string, Citation>;
  trace_id?: string;
}

interface QueryState {
  status: 'idle' | 'loading' | 'success' | 'error';
  result: QueryResult | null;
  error: string | null;
}

// ==========================================
// CONFIGURATION
// ==========================================

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'https://reguscope-api-773013301963.us-central1.run.app';

const EXAMPLE_QUERIES = [
  "What are the civil penalties for ITAR violations?",
  "Which agency enforces AECA regulations?",
  "What documentation is required for technical data transfers?",
  "What is the voluntary disclosure process for ITAR non-compliance?"
];

// ==========================================
// MAIN APP COMPONENT
// ==========================================

export default function ReguScopeApp() {
  const [query, setQuery] = useState('');
  const [queryState, setQueryState] = useState<QueryState>({
    status: 'idle',
    result: null,
    error: null
  });

  const handleSubmit = async () => {
    if (!query.trim()) return;

    setQueryState({ status: 'loading', result: null, error: null });

    try {
      const response = await fetch(`${API_URL}/compliance-query`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          user_query: query,
          user_id: `web_user_${Date.now()}`
        }),
      });

      if (!response.ok) {
        throw new Error(`API Error: ${response.status}`);
      }

      const data: QueryResult = await response.json();

      setQueryState({
        status: 'success',
        result: data,
        error: null
      });
    } catch (error) {
      setQueryState({
        status: 'error',
        result: null,
        error: error instanceof Error ? error.message : 'Unknown error occurred'
      });
    }
  };

  const handleExampleClick = (exampleQuery: string) => {
    setQuery(exampleQuery);
    setQueryState({ status: 'idle', result: null, error: null });
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100">
      {/* Header */}
      <header className="bg-white border-b border-slate-200 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="bg-blue-600 p-2 rounded-lg">
                <FileText className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-slate-900">ReguScope</h1>
                <p className="text-sm text-slate-600">AI-Powered Regulatory Compliance Analysis</p>
              </div>
            </div>
            <div className="flex items-center space-x-2 text-sm">
              <div className="flex items-center space-x-1 text-green-600 bg-green-50 px-3 py-1 rounded-full">
                <CheckCircle className="w-4 h-4" />
                <span className="font-medium">Operational</span>
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Query Interface */}
        <div className="bg-white rounded-xl shadow-lg p-6 mb-8">
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-2">
                Enter Your Compliance Question
              </label>
              <div className="relative">
                <textarea
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  onKeyDown={handleKeyPress}
                  placeholder="e.g., What are the export control requirements for technical data under ITAR?"
                  className="w-full px-4 py-3 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none text-slate-900 placeholder-slate-400"
                  rows={3}
                  disabled={queryState.status === 'loading'}
                />
              </div>
            </div>

            <div className="flex items-center justify-between">
              <button
                onClick={handleSubmit}
                disabled={queryState.status === 'loading' || !query.trim()}
                className="flex items-center space-x-2 px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-slate-300 disabled:cursor-not-allowed transition-colors font-medium"
              >
                {queryState.status === 'loading' ? (
                  <>
                    <Loader2 className="w-5 h-5 animate-spin" />
                    <span>Processing (60-90s)...</span>
                  </>
                ) : (
                  <>
                    <Search className="w-5 h-5" />
                    <span>Analyze Compliance</span>
                  </>
                )}
              </button>

              {queryState.status === 'loading' && (
                <div className="flex items-center space-x-2 text-sm text-amber-600">
                  <Clock className="w-4 h-4" />
                  <span>First query may take 60-90s (cold start)</span>
                </div>
              )}
            </div>
          </div>

          {/* Example Queries */}
          {queryState.status === 'idle' && (
            <div className="mt-6 pt-6 border-t border-slate-200">
              <p className="text-sm font-medium text-slate-700 mb-3">Example Questions:</p>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                {EXAMPLE_QUERIES.map((example, idx) => (
                  <button
                    key={idx}
                    onClick={() => handleExampleClick(example)}
                    className="text-left px-4 py-2 text-sm text-blue-600 bg-blue-50 rounded-lg hover:bg-blue-100 transition-colors"
                  >
                    {example}
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Loading State */}
        {queryState.status === 'loading' && (
          <div className="bg-white rounded-xl shadow-lg p-8 text-center">
            <Loader2 className="w-12 h-12 animate-spin text-blue-600 mx-auto mb-4" />
            <h3 className="text-lg font-semibold text-slate-900 mb-2">Analyzing Regulatory Documents</h3>
            <p className="text-slate-600 mb-4">Our AI agent is decomposing your query, retrieving relevant regulations, and synthesizing a comprehensive answer...</p>
            <div className="max-w-md mx-auto bg-slate-50 rounded-lg p-4">
              <div className="space-y-2 text-sm text-left text-slate-700">
                <div className="flex items-center space-x-2">
                  <div className="w-2 h-2 bg-blue-600 rounded-full animate-pulse"></div>
                  <span>Decomposing query into sub-questions</span>
                </div>
                <div className="flex items-center space-x-2">
                  <div className="w-2 h-2 bg-blue-600 rounded-full animate-pulse"></div>
                  <span>Retrieving relevant regulatory sections</span>
                </div>
                <div className="flex items-center space-x-2">
                  <div className="w-2 h-2 bg-blue-600 rounded-full animate-pulse"></div>
                  <span>Synthesizing answer with citations</span>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Error State */}
        {queryState.status === 'error' && (
          <div className="bg-red-50 border border-red-200 rounded-xl p-6">
            <div className="flex items-start space-x-3">
              <AlertCircle className="w-6 h-6 text-red-600 flex-shrink-0 mt-0.5" />
              <div>
                <h3 className="font-semibold text-red-900 mb-1">Error Processing Query</h3>
                <p className="text-red-700 mb-3">{queryState.error}</p>
                <button
                  onClick={() => setQueryState({ status: 'idle', result: null, error: null })}
                  className="text-sm text-red-600 hover:text-red-800 font-medium"
                >
                  Try Again
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Success State - Results */}
        {queryState.status === 'success' && queryState.result && (
          <div className="space-y-6">
            {/* Answer Section */}
            <div className="bg-white rounded-xl shadow-lg p-6">
              <div className="flex items-start justify-between mb-4">
                <h2 className="text-xl font-bold text-slate-900">Compliance Analysis</h2>
                {queryState.result.trace_id && (
                  <a
                    href={`https://cloud.langfuse.com/trace/${queryState.result.trace_id}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center space-x-1 text-sm text-blue-600 hover:text-blue-800"
                  >
                    <ExternalLink className="w-4 h-4" />
                    <span>View Trace</span>
                  </a>
                )}
              </div>
              
              <div className="prose prose-slate max-w-none">
                <div className="text-slate-800 leading-relaxed whitespace-pre-wrap">
                  {queryState.result.answer}
                </div>
              </div>
            </div>

            {/* Citations Section */}
            <div className="bg-white rounded-xl shadow-lg p-6">
              <h2 className="text-xl font-bold text-slate-900 mb-4">
                Source Citations ({Object.keys(queryState.result.citations).length})
              </h2>
              <div className="grid grid-cols-1 gap-4">
                {Object.entries(queryState.result.citations).map(([sourceId, citation]) => (
                  <CitationCard key={sourceId} sourceId={sourceId} citation={citation} />
                ))}
              </div>
            </div>

            {/* Action Buttons */}
            <div className="flex justify-center space-x-4">
              <button
                onClick={() => {
                  setQuery('');
                  setQueryState({ status: 'idle', result: null, error: null });
                }}
                className="px-6 py-3 bg-slate-600 text-white rounded-lg hover:bg-slate-700 transition-colors font-medium"
              >
                New Query
              </button>
            </div>
          </div>
        )}

        {/* Knowledge Base Info Banner */}
        {queryState.status === 'idle' && (
          <div className="mt-8 bg-blue-50 border border-blue-200 rounded-xl p-6">
            <div className="flex items-start space-x-3">
              <Info className="w-6 h-6 text-blue-600 flex-shrink-0 mt-0.5" />
              <div className="text-sm text-blue-900">
                <p className="font-semibold mb-2">About ReguScope's Knowledge Base</p>
                <p className="mb-3">
                  <strong>Current Demo Coverage:</strong> This system contains sample ITAR (International Traffic in Arms Regulations) 
                  and AECA (Arms Export Control Act) regulatory text for demonstration purposes.
                </p>
                <p className="mb-3">
                  <strong>Production Deployment Strategy:</strong> In a full production environment, the system would be pre-populated with:
                </p>
                <ul className="list-disc list-inside space-y-1 ml-4 mb-3">
                  <li>Complete ITAR regulations from state.gov (publicly available)</li>
                  <li>FDA 21 CFR compliance documents (public regulatory database)</li>
                  <li>EAR (Export Administration Regulations) from bis.doc.gov</li>
                  <li>ISO standards documentation (via commercial licensing)</li>
                  <li>Industry-specific compliance frameworks</li>
                </ul>
                <p className="mb-2">
                  <strong>Document Upload Feature (Roadmap):</strong> For Enterprise tier customers, we plan to add:
                </p>
                <ul className="list-disc list-inside space-y-1 ml-4">
                  <li>Private knowledge base creation for proprietary SOPs</li>
                  <li>PDF/Word document upload with automatic metadata extraction</li>
                  <li>Organization-specific compliance policy indexing</li>
                  <li>Multi-tenant data isolation with role-based access control</li>
                </ul>
                <p className="mt-3 text-xs text-blue-700">
                  <strong>Note:</strong> The current architecture supports these features - the RAGOps pipeline can ingest 
                  documents from any source. We are prioritizing core accuracy and observability before adding upload capabilities.
                </p>
              </div>
            </div>
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="mt-16 bg-white border-t border-slate-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex flex-col md:flex-row items-center justify-between text-sm text-slate-600 space-y-2 md:space-y-0">
            <p>© 2025 ReguScope - Production-Grade Agentic RAG Platform</p>
            <p>Powered by LangGraph · Qdrant · Phi-3 Mini · BGE-M3</p>
          </div>
        </div>
      </footer>
    </div>
  );
}

// ==========================================
// CITATION CARD COMPONENT
// ==========================================

function CitationCard({ sourceId, citation }: { sourceId: string; citation: Citation }) {
  const [isExpanded, setIsExpanded] = useState(false);

  return (
    <div className="border border-slate-200 rounded-lg p-4 hover:border-blue-300 transition-colors bg-white">
      {/* Header */}
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center space-x-2">
          <div className="bg-blue-100 text-blue-700 px-2 py-1 rounded text-xs font-bold uppercase">
            {sourceId.replace('source_', 'Source ')}
          </div>
          <h3 className="font-semibold text-slate-900">{citation.document_id}</h3>
        </div>
        <div className="flex items-center space-x-1 text-xs font-medium text-emerald-600 bg-emerald-50 px-2 py-1 rounded">
          <TrendingUp className="w-3 h-3" />
          <span>{(citation.relevance_score * 100).toFixed(1)}% Match</span>
        </div>
      </div>

      {/* Metadata Tags */}
      <div className="flex flex-wrap gap-2 mb-3">
        <div className="flex items-center space-x-1 text-xs bg-slate-100 text-slate-700 px-2.5 py-1 rounded-full">
          <Hash className="w-3 h-3" />
          <span>Section {citation.section_number}</span>
        </div>
        <div className="flex items-center space-x-1 text-xs bg-slate-100 text-slate-700 px-2.5 py-1 rounded-full">
          <MapPin className="w-3 h-3" />
          <span>{citation.jurisdiction}</span>
        </div>
        <div className="flex items-center space-x-1 text-xs bg-slate-100 text-slate-700 px-2.5 py-1 rounded-full">
          <Calendar className="w-3 h-3" />
          <span>Effective {citation.effective_date}</span>
        </div>
      </div>

      {/* Snippet */}
      <div className="text-sm text-slate-700 bg-slate-50 p-3 rounded border border-slate-200">
        <p className={isExpanded ? '' : 'line-clamp-3'}>
          {citation.snippet}
        </p>
        {citation.snippet.length > 150 && (
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="text-blue-600 hover:text-blue-800 text-xs font-medium mt-2 inline-flex items-center"
          >
            {isExpanded ? '← Show Less' : 'Show More →'}
          </button>
        )}
      </div>
    </div>
  );
}