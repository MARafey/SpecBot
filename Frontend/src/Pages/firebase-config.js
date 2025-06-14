// firebase-config.js
import { initializeApp } from "firebase/app";
import { getAuth, GoogleAuthProvider, GithubAuthProvider } from "firebase/auth";

const firebaseConfig = {
   apiKey: "AIzaSyCv_QGqW4TZOuqkQkT1CJ0yGzHbolzqe3o",
  authDomain: "specbot-79bfd.firebaseapp.com",
  projectId: "specbot-79bfd",
  storageBucket: "specbot-79bfd.firebasestorage.app",
  messagingSenderId: "1044853535348",
  appId: "1:1044853535348:web:07710e3ed112164a14d721",
  measurementId: "G-MCNR51TKJ3"
};

const app = initializeApp(firebaseConfig);
export const auth = getAuth(app);
export const googleProvider = new GoogleAuthProvider();
export const githubProvider = new GithubAuthProvider();
export default app;
