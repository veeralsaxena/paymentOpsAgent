
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { ArrowRight, Terminal, GitMerge, ShieldAlert, Zap, Cpu, Activity, ChevronRight } from "lucide-react";

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-[#000000] text-white overflow-hidden relative selection:bg-purple-500/30 font-sans">
      {/* Background Layers - Linear Style */}
      <div className="fixed inset-0 stars-bg opacity-40 pointer-events-none z-0" />
      <div className="fixed inset-0 bg-[radial-gradient(circle_at_center,_var(--tw-gradient-stops))] from-purple-900/10 via-transparent to-transparent opacity-50 z-0 pointer-events-none" />
      
      {/* Navigation */}
      <nav className="relative z-50 flex items-center justify-between px-6 py-6 md:px-12 max-w-[1400px] mx-auto bg-transparent">
        <div className="flex items-center gap-2 group cursor-pointer">
           <div className="w-6 h-6 rounded bg-gradient-to-br from-indigo-500 via-purple-500 to-pink-500 flex items-center justify-center shadow-[0_0_15px_rgba(168,85,247,0.4)] group-hover:shadow-[0_0_25px_rgba(168,85,247,0.6)] transition-all duration-500">
              <Activity className="w-4 h-4 text-white" />
           </div>
           <span className="text-sm font-semibold tracking-tight text-white/90 group-hover:text-white transition-colors">
             PaymentOps Agent
           </span>
        </div>
        <div className="hidden md:flex items-center gap-8 text-sm text-zinc-400 font-medium">
            <Link href="#architecture" className="hover:text-white transition-colors hover:drop-shadow-[0_0_8px_rgba(255,255,255,0.5)]">Architecture</Link>
            <Link href="#capabilities" className="hover:text-white transition-colors hover:drop-shadow-[0_0_8px_rgba(255,255,255,0.5)]">Capabilities</Link>
            <Link href="https://github.com/taqneeq/hackathon" target="_blank" className="hover:text-white transition-colors hover:drop-shadow-[0_0_8px_rgba(255,255,255,0.5)]">GitHub</Link>
        </div>
        <div>
            <Link href="/war-room">
                <Button variant="ghost" className="text-xs font-medium text-white/70 hover:text-white hover:bg-white/5 transition-all rounded-full h-8 px-4 border border-white/5 hover:border-white/20">
                    Log in <ChevronRight className="w-3 h-3 ml-1 opacity-50" />
                </Button>
            </Link>
        </div>
      </nav>

      {/* Hero Section */}
      <main className="relative z-10 pt-20 pb-32 px-6 md:pt-32 max-w-[1200px] mx-auto">
        <div className="flex flex-col items-center text-center">
            
            {/* Badge */}
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-white/5 border border-white/10 text-[11px] font-medium text-purple-200 mb-8 animate-in fade-in slide-in-from-bottom-4 duration-700 shadow-[0_0_15px_rgba(168,85,247,0.2)]">
               <span className="relative flex h-1.5 w-1.5">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-purple-400 opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-1.5 w-1.5 bg-purple-500"></span>
                </span>
               v2.0 Now Available
            </div>
            
            {/* Heading */}
            <h1 className="text-5xl md:text-8xl font-bold tracking-tight mb-8 leading-[1.05] animate-in fade-in slide-in-from-bottom-8 duration-1000 delay-100 bg-clip-text text-transparent bg-gradient-to-b from-white via-white/90 to-white/50 pb-2">
              The Self-Healing <br className="hidden md:block" />
              Financial Nervous System
            </h1>
            
            {/* Subtext */}
            <p className="text-lg md:text-xl text-zinc-400 max-w-2xl mx-auto mb-12 leading-relaxed animate-in fade-in slide-in-from-bottom-8 duration-1000 delay-200">
              Stop losing revenue to downtime. An autonomous agent that detects payment failures, reasons about root causes, and heals your infrastructure in milliseconds.
            </p>

            {/* CTA Buttons */}
            <div className="flex flex-col sm:flex-row items-center justify-center gap-4 animate-in fade-in slide-in-from-bottom-8 duration-1000 delay-300 mb-20">
                <Link href="/war-room">
                    <Button size="lg" className="h-12 px-8 bg-[#5E6AD2] hover:bg-[#4d5ac0] text-white rounded-full font-medium transition-all shadow-[0_0_40px_-10px_rgba(94,106,210,0.6)] hover:shadow-[0_0_60px_-15px_rgba(94,106,210,0.8)] border border-white/10 text-sm">
                       Launch Live Demo <ArrowRight className="ml-2 w-4 h-4" />
                    </Button>
                </Link>
                 <Button variant="ghost" size="lg" className="h-12 px-8 text-zinc-400 hover:text-white hover:bg-white/5 rounded-full font-medium border border-white/5 hover:border-white/10 text-sm">
                       View Documentation
                 </Button>
            </div>

            {/* Terminal Visual - Linear Style Glass */}
            <div className="w-full max-w-4xl animate-in fade-in slide-in-from-bottom-12 duration-1000 delay-500 perspective-1000">
                <div className="relative rounded-xl bg-[#0B0B14]/80 backdrop-blur-xl border border-white/10 shadow-[0_0_100px_-20px_rgba(120,50,255,0.2)] overflow-hidden group hover:border-white/20 transition-all duration-700">
                    
                    {/* Header */}
                    <div className="flex items-center justify-between px-4 py-3 bg-white/5 border-b border-white/5">
                        <div className="flex items-center gap-2">
                            <div className="w-3 h-3 rounded-full bg-[#FF5F57] shadow-sm" />
                            <div className="w-3 h-3 rounded-full bg-[#FEBC2E] shadow-sm" />
                            <div className="w-3 h-3 rounded-full bg-[#28C840] shadow-sm" />
                        </div>
                        <div className="text-[10px] text-zinc-500 font-mono tracking-widest uppercase opacity-50">agent-core-logic</div>
                        <div className="w-12" /> {/* Spacer */}
                    </div>
                    
                    {/* Content */}
                    <div className="p-6 font-mono text-xs md:text-sm space-y-3 text-left">
                        <div className="flex gap-2 items-center">
                            <span className="text-emerald-400">➜</span>
                            <span className="text-blue-400">~</span>
                            <span className="text-zinc-500">tail -f /var/log/payment-ops.log</span>
                        </div>
                        
                        <div className="space-y-1.5 pt-2">
                             <div className="flex gap-3 text-zinc-400/50">
                                <span className="opacity-50">14:32:01</span>
                                <span>[INFO] Heartbeat check: HDFC Gateway (24ms), SBI Gateway (31ms)</span>
                            </div>
                            <div className="flex gap-3 text-red-400/90 font-medium">
                                <span className="opacity-50">14:32:05</span>
                                <span>[ALERT] Payment failure detected (ID: PYMT-8721) | Error: &apos;Gateway Timeout&apos;</span>
                            </div>
                            <div className="flex gap-3 text-blue-400">
                                <span className="opacity-50">14:32:05</span>
                                <span>[AGENT] Initiating analysis... Contextual Bandits agent deployed.</span>
                            </div>
                             <div className="flex gap-3 text-purple-400">
                                <span className="opacity-50">14:32:06</span>
                                <span>[ACTION] Retrying payment via alternative route (Gateway: STRIPE_B) in 3, 2, 1...</span>
                            </div>
                             <div className="flex gap-3 text-emerald-400 font-bold">
                                <span className="opacity-50">14:32:07</span>
                                <span>[SUCCESS] Payment ID: PYMT-8721-B resolved. Real-time healing complete. Updating graph state.</span>
                            </div>
                        </div>
                        
                        <div className="flex gap-2 animate-pulse pt-2">
                            <span className="text-emerald-400">➜</span>
                            <span className="text-blue-400">~</span>
                            <span className="w-2 h-4 bg-zinc-600 block"></span>
                        </div>
                    </div>

                    {/* Gradient Overlay for Shine */}
                    <div className="absolute inset-0 bg-gradient-to-tr from-white/5 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-700 pointer-events-none" />
                </div>
            </div>
        </div>
      </main>

      {/* Bento Grid Features */}
      <section id="capabilities" className="relative z-10 py-32 px-6 max-w-[1200px] mx-auto">
         <div className="text-center mb-16">
            <h2 className="text-3xl md:text-5xl font-bold mb-4 tracking-tight">Built on Agentic Principles</h2>
            <p className="text-zinc-400 text-lg max-w-2xl mx-auto">
                Not a wrapper. A robust, stateful system designed for high-concurrency financial environments.
            </p>
         </div>

         <div className="grid grid-cols-1 md:grid-cols-3 gap-6 auto-rows-[300px]">
            {/* Card 1: LangGraph */}
            <div className="md:col-span-2 group relative p-8 rounded-3xl bg-[#0B0B14] border border-white/5 hover:border-white/10 transition-all duration-500 overflow-hidden flex flex-col justify-between hover:shadow-[0_0_50px_-20px_rgba(168,85,247,0.3)]">
                <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top_right,_var(--tw-gradient-stops))] from-purple-900/10 via-transparent to-transparent opacity-50" />
                <div className="relative z-10">
                    <div className="w-10 h-10 rounded-lg bg-white/5 flex items-center justify-center mb-6 border border-white/5">
                        <GitMerge className="w-5 h-5 text-purple-400" />
                    </div>
                    <h3 className="text-2xl font-bold mb-2 text-white/90">LangGraph State Machine</h3>
                    <p className="text-zinc-400 max-w-md text-sm leading-relaxed">
                        Deterministic control flow meets generative reasoning. The 
                        <span className="font-mono text-purple-300 bg-purple-500/10 px-1.5 py-0.5 rounded mx-1 text-xs">Observe</span> → 
                        <span className="font-mono text-purple-300 bg-purple-500/10 px-1.5 py-0.5 rounded mx-1 text-xs">Reason</span> → 
                        <span className="font-mono text-purple-300 bg-purple-500/10 px-1.5 py-0.5 rounded mx-1 text-xs">Act</span> 
                        loop ensures every action is auditable and reversible.
                    </p>
                </div>
                {/* Visual Representation */}
                <div className="relative h-16 w-full flex items-center gap-3 opacity-40 font-mono text-[10px]">
                    <div className="h-6 px-2 rounded border border-white/20 flex items-center bg-white/5">START</div>
                    <div className="h-px w-6 bg-white/20" />
                    <div className="h-6 px-2 rounded border border-purple-500/50 bg-purple-500/10 text-purple-300 flex items-center shadow-[0_0_10px_rgba(168,85,247,0.2)]">OBSERVE</div>
                    <div className="h-px w-6 bg-white/20" />
                    <div className="h-6 px-2 rounded border border-white/20 flex items-center bg-white/5">...</div>
                </div>
            </div>

            {/* Card 2: ML */}
            <div className="group relative p-8 rounded-3xl bg-[#0B0B14] border border-white/5 hover:border-white/10 transition-all duration-500 overflow-hidden hover:shadow-[0_0_50px_-20px_rgba(16,185,129,0.3)]">
                <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_bottom_left,_var(--tw-gradient-stops))] from-emerald-900/10 via-transparent to-transparent opacity-50" />
                <div className="relative z-10">
                    <div className="w-10 h-10 rounded-lg bg-white/5 flex items-center justify-center mb-6 border border-white/5">
                        <Cpu className="w-5 h-5 text-emerald-400" />
                    </div>
                    <h3 className="text-2xl font-bold mb-2 text-white/90">Contextual Bandits</h3>
                    <p className="text-zinc-400 text-sm leading-relaxed">
                        It maximizes utility. The RL model learns the optimal routing strategy for every bin/amount combination, balancing cost vs. success rate.
                    </p>
                </div>
            </div>

            {/* Card 3: Real-time */}
            <div className="group relative p-8 rounded-3xl bg-[#0B0B14] border border-white/5 hover:border-white/10 transition-all duration-500 overflow-hidden hover:shadow-[0_0_50px_-20px_rgba(59,130,246,0.3)]">
                 <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-blue-900/10 via-transparent to-transparent opacity-50" />
                <div className="relative z-10">
                    <div className="w-10 h-10 rounded-lg bg-white/5 flex items-center justify-center mb-6 border border-white/5">
                        <Zap className="w-5 h-5 text-blue-400" />
                    </div>
                    <h3 className="text-2xl font-bold mb-2 text-white/90">Sub-Second Healing</h3>
                    <p className="text-zinc-400 text-sm leading-relaxed mb-4">
                        Streaming data via Redis allows the agent to react to anomalies before they cascade.
                    </p>
                    <div className="inline-flex items-center gap-2 px-2 py-1 rounded bg-blue-500/10 border border-blue-500/20 text-xs font-mono text-blue-300">
                        <Activity className="w-3 h-3" /> Latency &lt; 50ms
                    </div>
                </div>
            </div>

             {/* Card 4: Human in the Loop (Wide) */}
             <div className="md:col-span-2 group relative p-8 rounded-3xl bg-[#0B0B14] border border-white/5 hover:border-white/10 transition-all duration-500 overflow-hidden flex items-center hover:shadow-[0_0_50px_-20px_rgba(245,158,11,0.3)]">
                 <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_right,_var(--tw-gradient-stops))] from-amber-900/10 via-transparent to-transparent opacity-50" />
                <div className="relative z-10 max-w-lg">
                    <div className="w-10 h-10 rounded-lg bg-white/5 flex items-center justify-center mb-6 border border-white/5">
                        <ShieldAlert className="w-5 h-5 text-amber-400" />
                    </div>
                    <h3 className="text-2xl font-bold mb-2 text-white/90">Human-in-the-Loop Guardrails</h3>
                    <p className="text-zinc-400 text-sm leading-relaxed">
                        Critical interventions (like blocking a gateway) scale difficulty based on risk. High-stakes actions require manual approval via the War Room dashboard, ensuring safety at scale.
                    </p>
                </div>
            </div>
         </div>
      </section>
      
       {/* Footer */}
       <footer className="relative z-10 py-12 px-6 border-t border-white/5 bg-[#050510]">
           <div className="max-w-[1200px] mx-auto flex flex-col md:flex-row justify-between items-center text-zinc-600 text-sm">
               <p>© 2026 PaymentOps Agent Project. Built for Taqneeq Hackathon.</p>
               <div className="flex gap-6 mt-4 md:mt-0">
                   <Link href="#" className="hover:text-zinc-400 transition-colors">Documentation</Link>
                   <Link href="#" className="hover:text-zinc-400 transition-colors">API Reference</Link>
                   <Link href="#" className="hover:text-zinc-400 transition-colors">Team</Link>
               </div>
           </div>
       </footer>
    </div>
  );
}
