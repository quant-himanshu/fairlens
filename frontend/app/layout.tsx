import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "FairLens — AI Bias Detection",
  description: "Detect, explain, and fix bias in AI decision systems before they harm real people.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className={`${inter.className} antialiased`}>
        <nav className="border-b border-gray-100 bg-white sticky top-0 z-50">
          <div className="max-w-6xl mx-auto px-4 h-14 flex items-center justify-between">
            <a href="/" className="flex items-center gap-2">
              <div className="w-7 h-7 rounded-lg bg-purple-600 flex items-center justify-center">
                <span className="text-white text-xs font-bold">FL</span>
              </div>
              <span className="font-semibold text-gray-900 text-sm">FairLens</span>
            </a>
            <div className="flex items-center gap-4">
              <span className="text-xs text-gray-400 hidden sm:block">AI Bias Detection Platform</span>
              <a
                href="https://github.com"
                className="text-xs text-gray-500 hover:text-gray-800 transition-colors"
              >
                GitHub
              </a>
            </div>
          </div>
        </nav>
        <main>{children}</main>
      </body>
    </html>
  );
}
