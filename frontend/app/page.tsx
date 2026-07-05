'use client';

import { useState, useEffect } from 'react';

interface Lead {
  id: string;
  website: string;
  email: string;
  selected: boolean;
}

export default function Home() {
  // Navigation View State: 'landing' or 'dashboard'
  const [view, setView] = useState<'landing' | 'dashboard'>('landing');
  
  // Animation States
  const [isMounted, setIsMounted] = useState(false);
  const [animateDashboard, setAnimateDashboard] = useState(false);

  // Trigger landing page animation on mount
  useEffect(() => {
    setIsMounted(true);
  }, []);

  // Trigger dashboard animation when view switches
  useEffect(() => {
    if (view === 'dashboard') {
      // Small timeout ensures the DOM node renders before applying transition classes
      const timer = setTimeout(() => setAnimateDashboard(true), 50);
      return () => clearTimeout(timer);
    } else {
      setAnimateDashboard(false);
    }
  }, [view]);

  // Scraper State
  const [query, setQuery] = useState('');
  const [maxResults, setMaxResults] = useState(10);
  const [leads, setLeads] = useState<Lead[]>([]);
  const [isScraping, setIsScraping] = useState(false);

  // Email State
  const [subject, setSubject] = useState('Automate Your Business & Save Hours Every Week');
  const [body, setBody] = useState("Hi there,\n\nI came across your website and loved your work. I wanted to reach out regarding a quick collaboration opportunity...\n\nBest,\nYonas");
  const [isSending, setIsSending] = useState(false);
  const [statusMessage, setStatusMessage] = useState('');
  const [statusType, setStatusType] = useState<'info' | 'success' | 'error' | ''>('');

  const handleSearch = async () => {
    setIsScraping(true);
    setStatusMessage('Launching stealth engine...');
    setStatusType('info');
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/scrape`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query, max_results: maxResults }),
      });
      
      const data = await response.json();
      
      if (data.status === 'success') {
        const formattedLeads: Lead[] = [];
        data.data.forEach((item: any) => {
          item.emails.forEach((email: string) => {
            formattedLeads.push({
              id: email + item.website,
              website: item.website,
              email: email,
              selected: true,
            });
          });
        });
        setLeads(formattedLeads);
        setStatusMessage(`Successfully found ${formattedLeads.length} leads.`);
        setStatusType('success');
      } else {
        setStatusMessage('Scraping failed: ' + data.detail);
        setStatusType('error');
      }
    } catch (error) {
      setStatusMessage('Could not connect to backend server.');
      setStatusType('error');
    }
    setIsScraping(false);
  };

  const handleSend = async () => {
    const selectedEmails = leads.filter(l => l.selected).map(l => l.email);
    
    if (selectedEmails.length === 0) {
      setStatusMessage('Please select at least one lead.');
      setStatusType('error');
      return;
    }

    setIsSending(true);
    setStatusMessage('Dispatching campaign outbox...');
    setStatusType('info');
    
    try {
      const response = await fetch('http://localhost:8000/api/send', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ target_emails: selectedEmails, subject, body }),
      });
      
      const data = await response.json();
      if (data.status === 'success') {
        setStatusMessage(data.message);
        setStatusType('success');
      } else {
        setStatusMessage('Failed to deliver campaign.');
        setStatusType('error');
      }
    } catch (error) {
      setStatusMessage('Connection failed during delivery.');
      setStatusType('error');
    }
    setIsSending(false);
  };

  const toggleLead = (id: string) => {
    setLeads(leads.map(lead => lead.id === id ? { ...lead, selected: !lead.selected } : lead));
  };

  const toggleAllLeads = () => {
    const allSelected = leads.every(l => l.selected);
    setLeads(leads.map(l => ({ ...l, selected: !allSelected })));
  };

  return (
    <div className="relative min-h-screen text-slate-900 antialiased selection:bg-blue-500/10 overflow-x-hidden font-sans">
      
      {/* SaaS Dotted Background Context */}
      <div className="absolute inset-0 -z-10 h-full w-full bg-slate-50 bg-[radial-gradient(#cbd5e1_1px,transparent_1px)] [background-size:24px_24px]">
        <div className="absolute bottom-0 left-0 right-0 top-1/2 bg-gradient-to-b from-transparent to-slate-50 opacity-90"></div>
      </div>
      
      {/* Global Status Banner Notification */}
      <div className={`absolute top-0 w-full transition-all duration-500 ease-in-out z-50 ${statusMessage && view === 'dashboard' ? 'translate-y-0 opacity-100' : '-translate-y-full opacity-0'}`}>
        <div className={`text-center py-2.5 px-4 text-xs font-medium border-b shadow-sm ${
          statusType === 'success' ? 'bg-emerald-50 text-emerald-700 border-emerald-100' :
          statusType === 'error' ? 'bg-rose-50 text-rose-700 border-rose-100' :
          'bg-blue-50 text-blue-700 border-blue-100'
        }`}>
          <div className="flex items-center justify-center gap-2">
            <span className={`h-1.5 w-1.5 rounded-full ${isScraping || isSending ? 'animate-ping' : ''} ${
              statusType === 'success' ? 'bg-emerald-500' :
              statusType === 'error' ? 'bg-rose-500' : 'bg-blue-500'
            }`} />
            {statusMessage}
          </div>
        </div>
      </div>

      {/* VIEW ONE: PREMIUM LANDING PAGE */}
      {view === 'landing' && (
        <div className={`max-w-6xl mx-auto px-6 py-20 min-h-screen flex flex-col justify-between transition-all duration-700 ease-in-out ${
          isMounted ? 'translate-y-0 opacity-100' : 'translate-y-8 opacity-0'
        }`}>
          {/* Landing Header */}
          <header className="flex items-center justify-between w-full">
            <div className="flex items-center gap-2.5">
              <div className="h-8 w-8 rounded-xl bg-gradient-to-br from-slate-800 to-black flex items-center justify-center text-white font-bold text-sm tracking-wider shadow-md">R</div>
              <span className="text-xl font-semibold tracking-tight text-slate-900">Reechly</span>
            </div>
            <button 
              onClick={() => setView('dashboard')}
              className="text-xs font-medium bg-white hover:bg-slate-50 border border-slate-200 shadow-sm px-4 py-2 rounded-xl transition-all active:scale-95"
            >
              Sign In
            </button>
          </header>

          {/* Hero Section */}
          <main className="my-auto text-center space-y-8 max-w-3xl mx-auto py-12">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-slate-900/5 border border-slate-900/10 text-xs font-medium text-slate-600 animate-fade-in">
              <span className="flex h-2 w-2 rounded-full bg-blue-500 animate-pulse"></span>
              Introducing Reechly v1.0
            </div>
            
            <h1 className="text-4xl sm:text-6xl font-extrabold tracking-tight text-slate-900 leading-[1.15] bg-clip-text">
              Automate your B2B lead generation <span className="bg-gradient-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent">in seconds</span>
            </h1>
            
            <p className="text-base sm:text-lg text-slate-500 max-w-xl mx-auto leading-relaxed">
              Find qualified business contacts, clean out the noise, and deploy targeted sequence pipelines from a single dashboard. 
            </p>

            <div className="pt-4">
              <button 
                onClick={() => setView('dashboard')}
                className="group relative bg-black hover:bg-slate-800 text-white text-sm px-8 py-4 rounded-xl font-medium shadow-xl shadow-black/10 transition-all transform active:scale-95 overflow-hidden inline-flex items-center gap-2"
              >
                <span>Get Started</span>
                <svg className="w-4 h-4 transition-transform group-hover:translate-x-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 5l7 7-7 7M5 5l7 7-7 7" />
                </svg>
              </button>
            </div>

            {/* Micro Feature Highlights Grid */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 pt-16 max-w-2xl mx-auto text-left">
              <div className="bg-white/60 backdrop-blur-md border border-slate-200/50 p-5 rounded-2xl shadow-sm">
                <div className="text-blue-600 font-semibold text-xs uppercase tracking-wider mb-1">01 / Deep Extract</div>
                <h3 className="text-sm font-semibold text-slate-800 mb-1">Contact Page Scanner</h3>
                <p className="text-xs text-slate-400 leading-normal">Deep scans site paths to locate hidden corporate profiles.</p>
              </div>
              <div className="bg-white/60 backdrop-blur-md border border-slate-200/50 p-5 rounded-2xl shadow-sm">
                <div className="text-indigo-600 font-semibold text-xs uppercase tracking-wider mb-1">02 / Clean Lead</div>
                <h3 className="text-sm font-semibold text-slate-800 mb-1">Smart Heuristics</h3>
                <p className="text-xs text-slate-400 leading-normal">Automatically strips media, support, and invalid system hooks.</p>
              </div>
              <div className="bg-white/60 backdrop-blur-md border border-slate-200/50 p-5 rounded-2xl shadow-sm">
                <div className="text-emerald-600 font-semibold text-xs uppercase tracking-wider mb-1">03 / Launch Outbox</div>
                <h3 className="text-sm font-semibold text-slate-800 mb-1">Direct Sequences</h3>
                <p className="text-xs text-slate-400 leading-normal">Send transactional sales layouts instantly to target files.</p>
              </div>
            </div>
          </main>

          {/* Footer Branding */}
          <footer className="text-center text-xs text-slate-400 pt-8 border-t border-slate-200/40">
            &copy; {new Date().getFullYear()} Reechly Inc. Built for lightning-fast outbound operations.
          </footer>
        </div>
      )}

      {/* VIEW TWO: APPLICATION WORKSPACE DASHBOARD */}
      {view === 'dashboard' && (
        <div className={`max-w-7xl mx-auto p-6 md:p-8 space-y-8 pt-16 transition-all duration-700 ease-out transform ${
          animateDashboard ? 'translate-y-0 opacity-100' : 'translate-y-8 opacity-0'
        }`}>
          
          {/* Dashboard Application Header */}
          <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 pb-6 border-b border-slate-200/60">
            <div>
              <div className="flex items-center gap-2.5">
                <button 
                  onClick={() => setView('landing')} 
                  className="mr-1 p-1.5 rounded-lg hover:bg-slate-200/60 transition-colors text-slate-400 hover:text-slate-700 group"
                  title="Return to Landing Page"
                >
                  <svg className="w-4 h-4 transform group-hover:-translate-x-0.5 transition-transform" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M10 19l-7-7m0 0l7-7m-7 7h18" />
                  </svg>
                </button>
                <div className="h-8 w-8 rounded-xl bg-gradient-to-br from-slate-800 to-black flex items-center justify-center text-white font-bold text-sm tracking-wider shadow-md">R</div>
                <h1 className="text-2xl font-semibold tracking-tight text-slate-900">Reechly</h1>
              </div>
              <p className="text-sm text-slate-500 mt-2">Autonomous B2B lead generation & dynamic cold outreach platform.</p>
            </div>
            
            <div className="flex items-center gap-4 text-xs text-slate-500 bg-white/60 backdrop-blur-md border border-slate-200/60 px-4 py-2 rounded-full shadow-sm">
              <div className="flex items-center gap-1.5">
                <span className="h-2 w-2 rounded-full bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.5)] animate-pulse" />
                Engine: <span className="font-semibold text-slate-700">Online</span>
              </div>
            </div>
          </div>

          {/* Dashboard Workspace Grid */}
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
            
            {/* Panel 1: Target Pipeline Extraction */}
            <div className="lg:col-span-7 bg-white/80 backdrop-blur-xl rounded-2xl border border-slate-200/60 shadow-xl shadow-slate-200/20 overflow-hidden flex flex-col transition-all duration-300 hover:shadow-2xl hover:shadow-slate-200/30">
              <div className="p-5 border-b border-slate-100/60 bg-white/50">
                <h2 className="text-xs font-bold uppercase tracking-widest text-slate-400">01 / Lead Acquisition</h2>
              </div>

              <div className="p-5 space-y-5">
                <div className="flex flex-col sm:flex-row gap-3">
                  <div className="relative flex-1 group">
                    <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                      <svg className="h-4 w-4 text-slate-400 group-focus-within:text-blue-500 transition-colors" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                      </svg>
                    </div>
                    <input 
                      type="text" 
                      placeholder="e.g., Real estate agencies in Dubai" 
                      className="w-full bg-slate-50/50 border border-slate-200 rounded-xl pl-10 pr-4 py-2.5 text-sm focus:bg-white focus:ring-4 focus:ring-blue-500/10 focus:border-blue-500 outline-none transition-all"
                      value={query}
                      onChange={(e) => setQuery(e.target.value)}
                    />
                  </div>
                  
                  <div className="flex gap-3">
                    <select 
                      className="bg-slate-50/50 border border-slate-200 rounded-xl px-3 py-2.5 text-sm outline-none focus:bg-white focus:ring-4 focus:ring-blue-500/10 focus:border-blue-500 transition-all text-slate-600 cursor-pointer"
                      value={maxResults}
                      onChange={(e) => setMaxResults(Number(e.target.value))}
                    >
                      <option value={10}>10 records</option>
                      <option value={20}>20 records</option>
                      <option value={50}>50 records</option>
                    </select>
                    
                    <button 
                      onClick={handleSearch}
                      disabled={isScraping || !query}
                      className="bg-black hover:bg-slate-800 active:bg-slate-900 text-white text-sm px-6 py-2.5 rounded-xl font-medium disabled:opacity-40 shadow-md shadow-black/10 transition-all flex items-center gap-2 whitespace-nowrap transform active:scale-95"
                    >
                      {isScraping ? 'Extracting...' : 'Run Scraper'}
                    </button>
                  </div>
                </div>

                {/* Extracted Leads Table Container */}
                <div className="border border-slate-200/60 rounded-xl overflow-hidden h-[420px] bg-slate-50/30 flex flex-col shadow-inner">
                  <div className="overflow-y-auto flex-1 custom-scrollbar">
                    <table className="w-full text-left border-separate border-spacing-0">
                      <thead className="bg-slate-50/80 backdrop-blur-md border-b border-slate-200 text-xs font-semibold uppercase tracking-wider text-slate-500 sticky top-0 z-10">
                        <tr>
                          <th className="px-5 py-4 w-12 text-center border-b border-slate-200/60">
                            <input 
                              type="checkbox"
                              checked={leads.length > 0 && leads.every(l => l.selected)}
                              onChange={toggleAllLeads}
                              className="w-4 h-4 text-black border-slate-300 rounded focus:ring-black/20 focus:ring-offset-0 cursor-pointer transition-all"
                            />
                          </th>
                          <th className="px-5 py-4 border-b border-slate-200/60">Found Email</th>
                          <th className="px-5 py-4 border-b border-slate-200/60">Source URL</th>
                        </tr>
                      </thead>
                      <tbody className="text-sm divide-y divide-slate-100/60 bg-white/40">
                        {leads.length === 0 ? (
                          <tr>
                            <td colSpan={3} className="px-4 py-32 text-center text-slate-400 text-xs max-w-md mx-auto">
                              {isScraping ? (
                                <div className="space-y-3 animate-pulse">
                                  <div className="mx-auto h-8 w-8 rounded-full border-2 border-slate-300 border-t-black animate-spin"></div>
                                  <p className="font-medium text-slate-600">Stealth browser initialized...</p>
                                </div>
                              ) : (
                                'No extracted records available. Initiate a search to generate targets.'
                              )}
                            </td>
                          </tr>
                        ) : (
                          leads.map((lead) => (
                            <tr key={lead.id} className="hover:bg-white transition-colors group">
                              <td className="px-5 py-3.5 text-center">
                                <input 
                                  type="checkbox" 
                                  checked={lead.selected}
                                  onChange={() => toggleLead(lead.id)}
                                  className="w-4 h-4 text-black border-slate-300 rounded focus:ring-black/20 focus:ring-offset-0 cursor-pointer transition-all"
                                />
                              </td>
                              <td className="px-5 py-3.5 font-medium text-slate-700 font-mono text-xs">{lead.email}</td>
                              <td className="px-5 py-3.5 text-slate-400 text-xs max-w-[240px] truncate" title={lead.website}>
                                <a href={lead.website} target="_blank" rel="noreferrer" className="hover:text-blue-600 hover:underline transition-colors">
                                  {lead.website.replace('https://', '').replace('http://', '').replace('www.', '')}
                                </a>
                              </td>
                            </tr>
                          ))
                        )}
                      </tbody>
                    </table>
                  </div>
                </div>
                
                <div className="flex items-center justify-between text-xs text-slate-400 pt-1 px-1">
                  <span>Total Staged: {leads.length}</span>
                  <span className="font-semibold text-black bg-slate-100 px-3 py-1 rounded-full">{leads.filter(l => l.selected).length} Targets Selected</span>
                </div>
              </div>
            </div>

            {/* Panel 2: Campaign Dispatch Sequence */}
            <div className="lg:col-span-5 bg-white/80 backdrop-blur-xl rounded-2xl border border-slate-200/60 shadow-xl shadow-slate-200/20 overflow-hidden flex flex-col transition-all duration-300 hover:shadow-2xl hover:shadow-slate-200/30">
              <div className="p-5 border-b border-slate-100/60 bg-white/50">
                <h2 className="text-xs font-bold uppercase tracking-widest text-slate-400">02 / Email Format</h2>
              </div>
              
              <div className="p-5 space-y-5 flex-1 flex flex-col">
                <div className="space-y-5 flex-1 flex flex-col">
                  <div>
                    <label className="block text-xs font-bold uppercase tracking-wider text-slate-500 mb-2">Subject Template</label>
                    <input 
                      type="text" 
                      className="w-full bg-slate-50/50 border border-slate-200 rounded-xl px-4 py-2.5 text-sm focus:bg-white focus:ring-4 focus:ring-blue-500/10 focus:border-blue-500 outline-none transition-all font-medium text-slate-800"
                      value={subject}
                      onChange={(e) => setSubject(e.target.value)}
                    />
                  </div>
                  
                  <div className="flex-1 flex flex-col">
                    <label className="block text-xs font-bold uppercase tracking-wider text-slate-500 mb-2">Message Body</label>
                    <textarea 
                      className="w-full flex-1 bg-slate-50/50 border border-slate-200 rounded-xl px-4 py-3 text-sm focus:bg-white focus:ring-4 focus:ring-blue-500/10 focus:border-blue-500 outline-none resize-none min-h-[300px] text-slate-700 leading-relaxed font-sans"
                      value={body}
                      onChange={(e) => setBody(e.target.value)}
                    />
                  </div>
                </div>

                <div className="pt-5 border-t border-slate-100/60 mt-auto">
                  <button 
                    onClick={handleSend}
                    disabled={isSending || leads.filter(l => l.selected).length === 0}
                    className="relative w-full overflow-hidden bg-black hover:bg-slate-800 active:bg-slate-900 text-white text-sm py-3.5 rounded-xl font-medium shadow-lg shadow-black/10 disabled:opacity-40 transition-all flex items-center justify-center gap-2 transform active:scale-[0.98] group"
                  >
                    <span className="relative z-10 flex items-center gap-2">
                      {isSending ? (
                        <>
                          <div className="h-4 w-4 rounded-full border-2 border-white/30 border-t-white animate-spin"></div>
                          Executing Sequence...
                      </>
                    ) : (
                      <>
                        <svg className="w-4 h-4 transition-transform group-hover:translate-x-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 5l7 7-7 7M5 5l7 7-7 7" />
                        </svg>
                        Send Bulk Email
                      </>
                    )}
                    </span>
                  </button>
                </div>
              </div>
            </div>

          </div>
        </div>
      )}
    </div>
  );
}