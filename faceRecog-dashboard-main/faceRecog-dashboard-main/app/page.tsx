"use client"

import dynamic from 'next/dynamic';

// Import the App component with SSR disabled since it uses browser APIs
const App = dynamic(() => import('../src/App'), {
  ssr: false
});

export default function HomePage() {
  return (
    <main className="min-h-screen">
      <App />
    </main>
  );
}