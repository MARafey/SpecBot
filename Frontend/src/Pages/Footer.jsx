import React from "react";
import "./Footer.css";

const Footer = () => {
  return (
    <footer className="footer">
      <a
        href="https://www.linkedin.com/in/ayra-alamdar/"
        className="social-link linkedin"
        target="_blank"
        rel="noopener noreferrer"
      >
        <img src="linkedin-logo.png" alt="LinkedIn" className="icon" />
      </a>
      <a
        href="https://github.com/ayra-alamdar/SpecBot"
        className="social-link github"
        target="_blank"
        rel="noopener noreferrer"
      >
        <img src="github-logo.jpg" alt="GitHub" className="icon" />
      </a>
      <a href="mailto:pcnlab@nu.edu.pk" className="social-link gmail">
        <img src="gmail-logo.png" alt="Gmail" className="icon" />
      </a>

      <div className="footer-text">
        <p>Copyright © 2024 SpecBot</p>
      </div>
    </footer>
  );
};

export default Footer;
