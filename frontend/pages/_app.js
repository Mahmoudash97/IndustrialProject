// /mnt/c/Users/asadi/Desktop/ChatBot/ChatBot_Reop/IndustrialProject/frontend/pages/_app.js
import Head from 'next/head'
import '../styles/globals.css'

export default function MyApp({ Component, pageProps }) {
  return (
    <>
      <Head>
        <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=0" />
      </Head>
      <Component {...pageProps} />
    </>
  )
}
