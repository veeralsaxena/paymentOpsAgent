import type { Metadata } from "next";
import { Sora, JetBrains_Mono } from "next/font/google";
import "./globals.css";

const sora = Sora({
  variable: "--font-sora",
  subsets: ["latin"],
});

const jetbrainsMono = JetBrains_Mono({
  variable: "--font-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Payment Operations War Room | Agentic AI",
  description: "Self-Healing Financial Nervous System - Real-time AI-powered payment operations management",
  keywords: ["payment operations", "agentic AI", "fintech", "LangGraph", "real-time monitoring"],
  authors: [{ name: "Taqneeq Hackathon Team" }],
  openGraph: {
    title: "Payment Operations War Room",
    description: "Self-Healing Financial Nervous System",
    type: "website",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark" suppressHydrationWarning>
      <body
        className={`${sora.variable} ${jetbrainsMono.variable} antialiased min-h-screen font-sans`}
      >
        {children}
      </body>
    </html>
  );
}
