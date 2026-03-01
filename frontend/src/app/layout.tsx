import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "AWS AI Webchat",
  description: "Webchat frontend for the FastAPI AWS assistant"
};

export default function RootLayout({
  children
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
