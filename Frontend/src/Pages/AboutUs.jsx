import React from "react";
import "./AboutUs.css";
import NavBar from "./NavBar";
import Footer from "./Footer";

const AboutUs = () => {
  return (
    <div className="about-container">
      <NavBar />
      <div className="about-content">
        <h1>About SpecBot</h1>
        <p>
          SpecBot is an advanced automation tool designed to generate optimized
          code based on user hardware specifications. Our mission is to
          streamline the coding process by automatically converting sequential
          code into efficient parallel implementations to achieve HPC.
        </p>

        <h2>Our Features</h2>
        <ul className="features">
          <li>Identifying parallelizable segments.</li>
          <li>Examining hardware specifications.</li>
          <li>Identifying computationally intensive code sections.</li>
          <li>Identifying data dependencies.</li>
          <li>Automating code parallelization.</li>
          <li>Assessing parallelized code performance.</li>
          <li>Displaying performance through comparison graphs.</li>
        </ul>

        <div className="workflow-section">
          <h2>Our Workflow</h2>
          <img
            src="/WorkFlow.png"
            alt="SpecBot Workflow Diagram"
            className="workflow-image"
          />
        </div>

        <div className="workflow-section">
          <h2>Our Algorithm - Parinomo's Workflow</h2>
          <img
            src="/Parinomo.png"
            alt="Parinomo's Algorithm Workflow"
            className="workflow-image"
          />
        </div>

        <h2>Our Team</h2>
        <p>
          SpecBot is developed by a dedicated team of engineers passionate about
          automation and optimization. Under the supervision of Dr. Arshad
          Islam, our team is continuously improving SpecBot to enhance developer
          efficiency.
        </p>

        <h3>Team Members</h3>
        <div className="team-container">
          <div className="team-member">
            <img
              src="/Rafey.png"
              alt="Muhammad Abdur Rafey"
              className="team-avatar"
            />
            <div className="team-name">Muhammad Abdur Rafey</div>
            <div className="team-id">m.a.rafey1215@gmail.com</div>
          </div>

          <div className="team-member">
            <img src="/Ayra.png" alt="Ayra Alamdar" className="team-avatar" />
            <div className="team-name">Ayra Alamdar</div>
            <div className="team-id">ayraalamdar309@gmail.com</div>
          </div>

          <div className="team-member">
            <img src="/Husnain.png" alt="Husnain Ali" className="team-avatar" />
            <div className="team-name">Husnain Ali</div>
            <div className="team-id">husnainali2721@gmail.com</div>
          </div>
        </div>

        <h3>Supervisor</h3>
        <div className="supervisor">
          <img
            src="/ArshadIslam.png"
            alt="Dr. Arshad Islam"
            className="team-avatar"
          />
          <div className="team-name">Dr. Arshad Islam</div>
        </div>

        <h3>Our Partners</h3>
        <div className="partner-logos">
          <img src="/PCN.png" alt="Partner 1" className="partner-logo" />
          <img src="/NU.png" alt="Partner 2" className="partner-logo" />
        </div>
      </div>
      <Footer />
    </div>
  );
};

export default AboutUs;
