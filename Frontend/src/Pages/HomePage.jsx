import React, { useEffect, useState } from "react";
import Navbar from "./NavBar";
import Footer from "./Footer";
import "./HomePage.css";
import { useNavigate } from "react-router-dom";
import { auth } from "./firebase-config";

const HomePage = () => {
  const navigate = useNavigate();
  const [user, setUser] = useState(null);

  // Check if the user is logged in
  useEffect(() => {
    const unsubscribe = auth.onAuthStateChanged((currentUser) => {
      setUser(currentUser);
    });
    return () => unsubscribe(); // Cleanup on unmount
  }, []);

  return (
    <div className="container">
      <Navbar user={user} />
      <div className="content-wrapper">
        <div className="content">
          <h1 className="heading-hp">
            Accelerate your Code's Performance with SpecBot!
          </h1>

          <div className="hero-section">
            <div className="hero-text">
              <h2>
                SpecBot's mission is to<br></br> streamline the coding<br></br>
                process by automatically<br></br> converting sequential code
                <br></br> into efficient parallel implementations to<br></br>
                achieve HPC (High<br></br> Performance Computing).
              </h2>
              {!user ? (
                <div className="login-cred">
                  <button
                    className="get-started-btn"
                    onClick={() => navigate("/login")}
                  >
                    Login
                  </button>
                </div>
              ) : (
                <button
                  className="get-started-btn"
                  onClick={() => navigate("/upload")}
                >
                  Get Started
                </button>
              )}
            </div>
            <div className="hero-image">
              <img src="./Graph.png" alt="SpecBot Illustration" />
            </div>
          </div>

          <h2 className="subheading">Why use SpecBot?</h2>
          <ul className="features">
            <li>Automates code parallelization for C/C++</li>
            <li>Enhances code performance for specific hardware setups</li>
            <li>Assesses parallelized code performance</li>
            <li>Displays performance through comparison graphs</li>
          </ul>

          <div className="promo-box">
            <h3>Get Started today for</h3>
            <h2>FREE!</h2>
            <p>Join us in making coding more efficient</p>
            <button
              className="try-free-btn"
              onClick={() => navigate("/upload")}
            >
              Try for Free
            </button>
          </div>

          <h2 className="extension-heading">
            Representation as an extension on Visual Studio Code
          </h2>
          <div className="demo-video">
            <video
              className="demo"
              controls
              width="80%"
              src="./Ext_working.mp4"
            >
              Your browser does not support the video tag.
            </video>
          </div>
        </div>
      </div>

      <Footer />
    </div>
  );
};

export default HomePage;
