import React from "react";
import { useNavigate } from "react-router-dom";
import "./NavBar.css"; // Ensure you have styles for the avatar and navbar

const NavBar = ({ user }) => {
  const navigate = useNavigate();

  return (
    <nav className="navbar">
      <div className="navbar-left">
        <img src="specbot-logo.png" alt="Logo" className="navbar-logo" />
        <span className="navbar-title" onClick={() => navigate("/")}>
          SpecBot
        </span>
      </div>
      <div className="navbar-links">
        <button className="nav-btn" onClick={() => navigate("/upload")}>
          Get Started
        </button>
        <button className="nav-btn" onClick={() => navigate("/about")}>
          About Us
        </button>
        <button className="nav-btn" onClick={() => navigate("/benchmarks")}>
          Benchmarks
        </button>
        {user ? (
          // Display the avatar when user is logged in
          <div className="avatar" title={user.email}>
            {user.email[0].toUpperCase()}
          </div>
        ) : (
          // Display Login button when user is not logged in
          <button className="login-btn" onClick={() => navigate("/login")}>
            Login
          </button>
        )}
      </div>
    </nav>
  );
};

export default NavBar;
