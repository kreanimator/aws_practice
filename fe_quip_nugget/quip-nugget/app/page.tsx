import Image from "next/image";
import styles from "./Home.module.css";
import QuipNugget from "../components/quip_nugget";

export default function Home() {
  return (
    <main>
    <div className= {styles.container} >
    <QuipNugget />
    </div>
    </main>
  );
};
