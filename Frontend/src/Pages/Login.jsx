import React, { useState } from "react";
import "./Login.css";
import NavBar from "./NavBar";
import Footer from "./Footer";
import { useNavigate } from "react-router-dom";
import { auth, googleProvider, githubProvider } from "./firebase-config";
import {
  signInWithPopup,
  signInWithEmailAndPassword,
  createUserWithEmailAndPassword,
} from "firebase/auth";

const LoginPage = () => {
  const navigate = useNavigate();
  const [isSignup, setIsSignup] = useState(false); // Toggle between Login and Signup modes
  const [formData, setFormData] = useState({
    email: "",
    password: "",
    name: "",
  });
  const [isLoading, setIsLoading] = useState(false); // Loading state for async operations
  const [error, setError] = useState(""); // Error state for validation or Firebase errors

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData({ ...formData, [name]: value });
  };

  const validateForm = () => {
    if (!formData.email || !formData.password || (isSignup && !formData.name)) {
      setError("Please fill out all required fields.");
      return false;
    }
    setError("");
    return true;
  };

  const handleEmailAuth = async () => {
    if (!validateForm()) return;

    setIsLoading(true);
    try {
      if (isSignup) {
        await createUserWithEmailAndPassword(
          auth,
          formData.email,
          formData.password
        );
        alert("Signup successful! Welcome to SpecBot.");
      } else {
        await signInWithEmailAndPassword(
          auth,
          formData.email,
          formData.password
        );
        alert("Login successful! Welcome back to SpecBot.");
      }
      navigate("/");
    } catch (error) {
      setError(error.message);
    } finally {
      setIsLoading(false);
    }
  };

  const handleOAuth = async (provider) => {
    setIsLoading(true);
    try {
      await signInWithPopup(auth, provider);
      alert("Authentication successful! Welcome to SpecBot.");
      navigate("/");
    } catch (error) {
      setError(error.message);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="login-container">
      <NavBar />
      <div className="content-wrapper">
        <div className="login-content">
          <h1>{isSignup ? "Sign Up for SpecBot!" : "Log In to SpecBot!"}</h1>
          <div className="login-box">
            {error && <p className="error-message">{error}</p>}
            {isSignup && (
              <input
                type="text"
                name="name"
                placeholder="Enter your name"
                className={`login-input ${
                  !formData.name && error ? "input-error" : ""
                }`}
                onChange={handleChange}
                aria-label="Name"
              />
            )}
            <input
              type="email"
              name="email"
              placeholder="Enter your email"
              className={`login-input ${
                !formData.email && error ? "input-error" : ""
              }`}
              onChange={handleChange}
              aria-label="Email"
            />
            <input
              type="password"
              name="password"
              placeholder="Enter your password"
              className={`login-input ${
                !formData.password && error ? "input-error" : ""
              }`}
              onChange={handleChange}
              aria-label="Password"
            />
            <button
              className="login-submit-btn"
              onClick={handleEmailAuth}
              disabled={isLoading}
            >
              {isLoading ? "Processing..." : isSignup ? "Sign Up" : "Log In"}
            </button>
            <p>Or {isSignup ? "sign up" : "log in"} using:</p>
            <div className="social-icons">
              <img
                src="/google-logo.png"
                alt="Sign in with Google"
                className="social-icon"
                onClick={() => handleOAuth(googleProvider)}
                role="button"
              />
              <img
                src="/github-logo.jpg"
                alt="Sign in with GitHub"
                className="social-icon"
                onClick={() => handleOAuth(githubProvider)}
                role="button"
              />
            </div>
            <p>
              {isSignup ? "Already have an account?" : "Don't have an account?"}{" "}
              <span
                className="toggle-link"
                onClick={() => setIsSignup(!isSignup)}
                role="button"
              >
                {isSignup ? "Log In" : "Sign Up"}
              </span>
            </p>
          </div>
        </div>
      </div>
      <Footer />
    </div>
  );
};

export default LoginPage;
